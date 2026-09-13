"""
Data distribution module for federated learning simulation.

Handles loading datasets and distributing them across simulated IoT clients
using IID and Non-IID (Dirichlet) partitioning strategies.
"""

import numpy as np
import torch
from torch.utils.data import DataLoader, Subset
import torchvision
import torchvision.transforms as transforms

from simulation.contracts import apply_lognormal_retention


def load_dataset(name, data_dir='./data'):
    """
    Load a dataset with appropriate transforms.

    Args:
        name: 'cifar10' or 'mnist'
        data_dir: directory to cache downloaded data

    Returns:
        (train_dataset, test_dataset)
    """
    if name == 'cifar10':
        transform_train = transforms.Compose([
            transforms.RandomHorizontalFlip(),
            transforms.RandomCrop(32, padding=4),
            transforms.ToTensor(),
            transforms.Normalize((0.4914, 0.4822, 0.4465),
                                 (0.2023, 0.1994, 0.2010)),
        ])
        transform_test = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.4914, 0.4822, 0.4465),
                                 (0.2023, 0.1994, 0.2010)),
        ])
        train_dataset = torchvision.datasets.CIFAR10(
            root=data_dir, train=True, download=True, transform=transform_train
        )
        test_dataset = torchvision.datasets.CIFAR10(
            root=data_dir, train=False, download=True, transform=transform_test
        )
    elif name == 'mnist':
        transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.1307,), (0.3081,)),
        ])
        train_dataset = torchvision.datasets.MNIST(
            root=data_dir, train=True, download=True, transform=transform
        )
        test_dataset = torchvision.datasets.MNIST(
            root=data_dir, train=False, download=True, transform=transform
        )
    elif name == 'fashion_mnist':
        transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.2860,), (0.3530,)),
        ])
        train_dataset = torchvision.datasets.FashionMNIST(
            root=data_dir, train=True, download=True, transform=transform
        )
        test_dataset = torchvision.datasets.FashionMNIST(
            root=data_dir, train=False, download=True, transform=transform
        )
    elif name == 'har':
        from simulation.har_loader import HARDataset
        har_dir = data_dir if data_dir.endswith('UCI_HAR') else f'{data_dir}/UCI_HAR'
        train_dataset = HARDataset(data_dir=har_dir, train=True, download=True)
        test_dataset = HARDataset(data_dir=har_dir, train=False, download=True)
    else:
        raise ValueError(f"Unknown dataset: {name}")

    return train_dataset, test_dataset


def distribute_iid(dataset, num_clients, seed=42):
    """
    Distribute dataset equally and randomly (IID) across clients.

    Args:
        dataset: PyTorch dataset
        num_clients: number of clients
        seed: random seed for reproducibility

    Returns:
        dict {client_id: list of sample indices}
    """
    rng = np.random.default_rng(seed)
    num_samples = len(dataset)
    indices = rng.permutation(num_samples)
    splits = np.array_split(indices, num_clients)
    return {i: splits[i].tolist() for i in range(num_clients)}


def distribute_non_iid(dataset, num_clients, alpha=0.5, seed=42):
    """
    Distribute dataset using Dirichlet distribution for Non-IID partitioning.

    This simulates real-world IoT scenarios where each device sees different
    data distributions. Lower alpha = more heterogeneous (Non-IID).

    - alpha → 0: Each client gets data from only 1-2 classes (extreme Non-IID)
    - alpha → ∞: Approaches IID distribution
    - alpha = 0.5: Moderate heterogeneity (recommended for IoT simulation)

    Args:
        dataset: PyTorch dataset
        num_clients: number of IoT clients
        alpha: Dirichlet concentration parameter
        seed: random seed

    Returns:
        dict {client_id: list of sample indices}
    """
    rng = np.random.default_rng(seed)

    # Extract labels
    if hasattr(dataset, 'targets'):
        labels = np.array(dataset.targets)
    elif hasattr(dataset, 'labels'):
        labels = np.array(dataset.labels)
    else:
        labels = np.array([dataset[i][1] for i in range(len(dataset))])

    num_classes = len(np.unique(labels))
    client_indices = {i: [] for i in range(num_clients)}

    # For each class, distribute its indices using Dirichlet
    for c in range(num_classes):
        class_indices = np.where(labels == c)[0]
        rng.shuffle(class_indices)

        # Sample proportions from Dirichlet distribution
        proportions = rng.dirichlet(np.repeat(alpha, num_clients))

        # Balance proportions so no client is too empty
        proportions = proportions / proportions.sum()

        # Split indices according to proportions
        proportions_cumsum = np.cumsum(proportions)
        split_points = (proportions_cumsum * len(class_indices)).astype(int)
        split_points = np.clip(split_points, 0, len(class_indices))

        splits = np.split(class_indices, split_points[:-1])

        for i, split in enumerate(splits):
            client_indices[i].extend(split.tolist())

    return client_indices


def create_client_loaders(dataset, client_indices, batch_size=32):
    """
    Create DataLoader objects for each client from their assigned indices.

    Args:
        dataset: PyTorch dataset
        client_indices: dict {client_id: list of sample indices}
        batch_size: batch size for DataLoader

    Returns:
        dict {client_id: DataLoader}
    """
    loaders = {}
    for client_id, indices in client_indices.items():
        if len(indices) > 0:
            subset = Subset(dataset, indices)
            loaders[client_id] = DataLoader(
                subset, batch_size=batch_size, shuffle=True
            )
        else:
            # Empty client — skip
            loaders[client_id] = None
    return loaders


def get_client_class_distribution(dataset, client_indices):
    """
    Get the class distribution for each client (for analysis/visualization).

    Args:
        dataset: PyTorch dataset
        client_indices: dict from distribute_* functions

    Returns:
        dict {client_id: {class_label: count}}
    """
    if hasattr(dataset, 'targets'):
        labels = np.array(dataset.targets)
    else:
        labels = np.array([dataset[i][1] for i in range(len(dataset))])

    distributions = {}
    for client_id, indices in client_indices.items():
        client_labels = labels[indices]
        unique, counts = np.unique(client_labels, return_counts=True)
        distributions[client_id] = dict(zip(unique.tolist(), counts.tolist()))

    return distributions


def extract_root_subset(client_indices, size=100, seed=42):
    """
    Hold out `size` samples from the union of client data — used as the clean
    "root" dataset for FLTrust (Cao et al., NDSS 2021).

    Removed indices are taken uniformly at random across all clients to avoid
    biasing toward any single client's distribution. The function returns the
    held-out indices and a new client_indices dict with those samples removed.

    Args:
        client_indices: dict {client_id: list of sample indices}
        size: number of samples to hold out
        seed: random seed

    Returns:
        (held_out_indices, new_client_indices)
    """
    rng = np.random.default_rng(seed)
    all_used = []
    for cid, idx_list in client_indices.items():
        for i in idx_list:
            all_used.append((cid, int(i)))
    if len(all_used) <= size:
        return [], client_indices
    chosen = rng.choice(len(all_used), size=size, replace=False).tolist()
    held_out_indices = [all_used[i][1] for i in sorted(chosen)]
    held_out_set = set(held_out_indices)
    new_client_indices = {
        cid: [i for i in idx_list if int(i) not in held_out_set]
        for cid, idx_list in client_indices.items()
    }
    return held_out_indices, new_client_indices


def apply_data_size_variance(client_indices, sigma=0.5, min_samples=20, seed=42,
                             empty_client_policy='preserve_empty'):
    """
    Apply lognormal variance to per-client data sizes (realistic IoT heterogeneity).

    Real IoT devices have wildly varying data volumes — a wearable might log 50
    samples per day while a smart-home hub logs 5000. Pure Dirichlet partitioning
    gives roughly equal-sized clients; this function rescales each client's index
    list using a lognormal multiplier clipped at 1.0 (we cannot synthesize new
    samples). Non-empty clients retain a ``min_samples`` floor when possible;
    already-empty clients remain empty under the explicit preserve-empty policy.

    Args:
        client_indices: dict {client_id: list of indices}
        sigma: lognormal sigma (0.5 = moderate, 1.0 = high variance)
        min_samples: minimum samples per client
        seed: random seed

    Returns:
        dict {client_id: list of indices} with rescaled (subsampled) sizes
    """
    return apply_lognormal_retention(
        client_indices,
        sigma=sigma,
        min_samples=min_samples,
        seed=seed,
        empty_client_policy=empty_client_policy,
    )


def repair_minimum_partition(client_indices, minimum=20, seed=42):
    """Move existing unique samples from largest donors; preserve the union."""
    result = {cid: list(values) for cid, values in sorted(client_indices.items())}
    flat = [i for values in result.values() for i in values]
    if len(flat) != len(set(flat)):
        raise ValueError("partition contains duplicated examples")
    if len(flat) < minimum * len(result):
        raise ValueError("insufficient retained samples for minimum repair")
    rng = np.random.default_rng(seed)
    moved = 0
    for cid in result:
        while len(result[cid]) < minimum:
            donor = max(result, key=lambda key: (len(result[key]), -key))
            take = min(minimum - len(result[cid]), len(result[donor]) - minimum)
            positions = set(int(i) for i in rng.choice(len(result[donor]), take, replace=False))
            result[cid].extend(v for i, v in enumerate(result[donor]) if i in positions)
            result[donor] = [v for i, v in enumerate(result[donor]) if i not in positions]
            moved += take
    return result, moved
