"""
UCI HAR (Human Activity Recognition) Dataset loader.

Downloads and parses the UCI HAR dataset (Anguita et al., 2013) used in
FLTrust (Cao et al., NDSS 2021) as a wearable IoT benchmark. 561 hand-crafted
features per window, 6 activity classes:
    1 WALKING, 2 WALKING_UPSTAIRS, 3 WALKING_DOWNSTAIRS,
    4 SITTING,  5 STANDING,        6 LAYING.

Train: ~7352 windows from 21 subjects. Test: ~2947 windows from 9 subjects.
The dataset is intrinsically heterogeneous because each subject has a unique
movement signature — a natural fit for federated IoT simulation.
"""

import os
import urllib.request
import zipfile

import numpy as np
import torch
from torch.utils.data import Dataset


UCI_HAR_URL = (
    "https://archive.ics.uci.edu/ml/machine-learning-databases/00240/"
    "UCI%20HAR%20Dataset.zip"
)


class HARDataset(Dataset):
    """UCI HAR train/test split as a torch Dataset.

    Args:
        data_dir: cache directory (will hold UCI_HAR_Dataset/ after extraction)
        train:    True → train split, False → test split
        download: download + extract if files are absent
    """

    NUM_CLASSES = 6
    FEATURE_DIM = 561

    def __init__(self, data_dir='./data/UCI_HAR', train=True, download=True):
        self.data_dir = data_dir
        self.train = train

        if download:
            self._maybe_download()

        split = 'train' if train else 'test'
        # The zip extracts into "UCI HAR Dataset/" with a literal space.
        root = os.path.join(self.data_dir, 'UCI HAR Dataset')
        x_path = os.path.join(root, split, f'X_{split}.txt')
        y_path = os.path.join(root, split, f'y_{split}.txt')

        if not (os.path.exists(x_path) and os.path.exists(y_path)):
            raise FileNotFoundError(
                f"UCI HAR files not found at {root}. "
                f"Set download=True or fetch manually from {UCI_HAR_URL}"
            )

        self.X = np.loadtxt(x_path, dtype=np.float32)
        # Labels in file are 1..6 — shift to 0..5 for CrossEntropyLoss.
        self.y = (np.loadtxt(y_path, dtype=np.int64) - 1)
        # `targets` exposes label list for compatibility with
        # data_distributor.distribute_non_iid (which expects .targets or .labels).
        self.targets = self.y.tolist()

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        x = torch.from_numpy(self.X[idx]).float()
        y = int(self.y[idx])
        return x, y

    def _maybe_download(self):
        root = os.path.join(self.data_dir, 'UCI HAR Dataset')
        if os.path.isdir(root):
            return
        os.makedirs(self.data_dir, exist_ok=True)
        zip_path = os.path.join(self.data_dir, 'UCI_HAR.zip')
        print(f"[HAR] Downloading UCI HAR Dataset → {zip_path}")
        urllib.request.urlretrieve(UCI_HAR_URL, zip_path)
        print(f"[HAR] Extracting to {self.data_dir}")
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(self.data_dir)
        os.remove(zip_path)
        print(f"[HAR] Ready: {root}")
