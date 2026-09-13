"""
Federated learning client module.

Each Client instance simulates an IoT device that:
    1. Holds a private local dataset
    2. Trains a model on its local data
    3. Sends gradient updates to the central server

Supports both benign and malicious (poisoning) behaviors.
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from simulation.models import get_model_weights, set_model_weights
from simulation.contracts import stealth_gaussian_perturbation


class Client:
    """
    Simulates a single IoT client/device in the federated network.

    Args:
        client_id: unique identifier
        data_loader: PyTorch DataLoader for local training data
        model_fn: callable that returns a new model instance
        device: torch device ('cpu' or 'cuda')
        is_malicious: whether this client performs poisoning attacks
        attack_type: type of poisoning attack ('label_flip', 'gaussian', 'scale')
    """

    def __init__(self, client_id, data_loader, model_fn, device='cpu',
                 is_malicious=False, attack_type='gaussian', attack_params=None):
        self.client_id = client_id
        self.data_loader = data_loader
        self.device = device
        self.is_malicious = is_malicious
        self.attack_type = attack_type
        self.attack_params = dict(attack_params or {})

        # Initialize local model
        self.model = model_fn().to(self.device)
        self.criterion = nn.CrossEntropyLoss()

    def train(self, global_weights, epochs=5, lr=0.01, num_classes=10,
              optimizer_momentum=0.9, max_local_steps=None, rng_seed=None):
        """
        Perform local training starting from global weights.

        Args:
            global_weights: numpy array of global model weights
            epochs: number of local training epochs
            lr: learning rate
            num_classes: number of classes in the dataset (for label_flip attack)

        Returns:
            gradient_update: numpy array (local_weights - global_weights)
        """
        if rng_seed is not None:
            # Isolate minibatch shuffle, augmentations and model dropout.
            with torch.random.fork_rng():
                torch.manual_seed(rng_seed)
                return self.train(global_weights, epochs, lr, num_classes,
                                  optimizer_momentum, max_local_steps, None)
        # Load global weights
        set_model_weights(self.model, global_weights)

        # Set up optimizer
        optimizer = optim.SGD(
            self.model.parameters(), lr=lr, momentum=optimizer_momentum,
        )

        # Train locally
        self.model.train()
        steps = 0
        training_epochs = (epochs if max_local_steps is None else
                           (max_local_steps + len(self.data_loader) - 1) // len(self.data_loader))
        for epoch in range(training_epochs):
            for batch_data, batch_labels in self.data_loader:
                batch_data = batch_data.to(self.device)
                batch_labels = batch_labels.to(self.device)

                # Label flip attack: reverse labels during training
                # This is a DATA-level poisoning — the gradient itself looks
                # "legitimately trained" but pushes the model in the wrong direction.
                if self.is_malicious and self.attack_type == 'label_flip':
                    batch_labels = (num_classes - 1) - batch_labels

                if self.is_malicious and self.attack_type == 'patch_backdoor':
                    from simulation.audit_attacks import stamp_trigger
                    target = self.attack_params['backdoor_target']
                    rng = self.attack_params['rng']
                    eligible = (batch_labels != target).nonzero().flatten()
                    mask = rng.random(len(eligible)) < self.attack_params['backdoor_fraction']
                    selected = eligible[torch.as_tensor(mask, device=eligible.device)]
                    if len(selected):
                        batch_data = batch_data.clone()
                        batch_labels = batch_labels.clone()
                        batch_data[selected] = stamp_trigger(batch_data[selected], self.attack_params['dataset'],
                                                             self.attack_params['backdoor_patch_size'])
                        batch_labels[selected] = target

                optimizer.zero_grad()
                outputs = self.model(batch_data)
                loss = self.criterion(outputs, batch_labels)
                loss.backward()
                optimizer.step()
                steps += 1
                if max_local_steps is not None and steps >= max_local_steps:
                    break
            if max_local_steps is not None and steps >= max_local_steps:
                break

        # Compute gradient update (delta = local_weights - global_weights)
        local_weights = get_model_weights(self.model)
        gradient_update = local_weights - global_weights
        self.last_optimizer_steps = steps

        clean_update = gradient_update
        self.last_attack_diagnostics = {'attack_type': self.attack_type,
                                        'is_malicious': bool(self.is_malicious)}
        if self.is_malicious and self.attack_type not in ('label_flip', 'patch_backdoor', 'minmax_omniscient', 'minsum_omniscient'):
            gradient_update = self._poison_gradient(gradient_update)
            clean64 = clean_update.astype(np.float64)
            poisoned64 = gradient_update.astype(np.float64)
            clean_norm = float(np.linalg.norm(clean64))
            poisoned_norm = float(np.linalg.norm(poisoned64))
            perturbation_norm = float(np.linalg.norm(poisoned64 - clean64))
            self.last_attack_diagnostics.update({
                'comparable_clean_delta': True,
                'clean_norm': clean_norm, 'poisoned_norm': poisoned_norm,
                'perturbation_norm': perturbation_norm,
                'relative_perturbation': perturbation_norm / clean_norm if clean_norm else None,
                'cosine': float(np.clip(np.dot(clean64, poisoned64) / (clean_norm * poisoned_norm), -1, 1)) if clean_norm and poisoned_norm else None,
            })
        elif self.is_malicious:
            self.last_attack_diagnostics.update({'comparable_clean_delta': False,
                                                'reason': 'data_poisoning_or_coordinated_evaluator_attack'})

        return gradient_update

    def _poison_gradient(self, gradient):
        """
        Apply poisoning attack to the gradient update.

        Attack types:
            - 'gaussian':           Loud Gaussian noise σ=5 (norm explodes ~10⁴×).
                                    Norm-based filters detect it trivially.
            - 'stealth_gaussian':   Canonical random-direction perturbation whose
                                    total L2 norm is rho * ||g|| (rho=0.005).
            - 'adaptive_gaussian':  Legacy name for bounded random-direction noise.
                                    g̃ = g + α · v_attack, where v_attack is
                                    a random unit direction scaled by the
                                    benign norm × α (default α=0.3).
                                    Attacker assumes the defense exists and
                                    keeps norm close to benign while distorting
                                    direction.
            - 'scale':              Scale by -10 (legacy strong byzantine).
            - 'sign_flip':          Flip sign (legacy byzantine).
        """
        rng = self.attack_params.get("rng", np.random)
        if self.attack_type == 'gaussian':
            noise = rng.normal(
                0, self.attack_params.get('gaussian_std', 5.0), size=gradient.shape
            ).astype(gradient.dtype, copy=False)
            result = gradient + noise
            if not np.all(np.isfinite(result)):
                raise ValueError('gaussian attack produced a non-finite update')
            return result.astype(gradient.dtype, copy=False)
        elif self.attack_type == 'stealth_gaussian':
            return stealth_gaussian_perturbation(
                gradient, rho=self.attack_params.get('stealth_rho', 0.005), rng=rng
            )
        elif self.attack_type == 'adaptive_gaussian':
            alpha = self.attack_params.get('adaptive_alpha', 0.3)
            g_norm = float(np.linalg.norm(gradient))
            rand_dir = rng.normal(size=gradient.shape).astype(
                gradient.dtype, copy=False,
            )
            rand_dir /= max(np.linalg.norm(rand_dir), 1e-10)
            adversarial = rand_dir * g_norm * alpha
            result = gradient + adversarial.astype(gradient.dtype, copy=False)
            if not np.all(np.isfinite(result)):
                raise ValueError('adaptive attack produced a non-finite update')
            return result.astype(gradient.dtype, copy=False)
        elif self.attack_type == 'scale':
            return gradient * -10.0
        elif self.attack_type == 'sign_flip':
            return -gradient
        else:
            return gradient

    def get_data_size(self):
        """Return the number of local training samples."""
        if self.data_loader is None:
            return 0
        return len(self.data_loader.dataset)
