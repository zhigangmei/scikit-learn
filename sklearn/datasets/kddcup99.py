"""KDDCUP 99 dataset.

A classic dataset for anomaly detection.

The dataset page is available from UCI Machine Learning Repository

https://archive.ics.uci.edu/ml/machine-learning-databases/kddcup99-mld/kddcup.data.gz

"""

import errno
from gzip import GzipFile
import logging
import os
from os.path import dirname, exists, join

import numpy as np


from .base import _fetch_remote
from .base import get_data_home
from .base import RemoteFileMetadata
from ..utils import Bunch
from ..utils import _joblib
from ..utils import check_random_state
from ..utils import shuffle as shuffle_method

# The original data can be found at:
# https://archive.ics.uci.edu/ml/machine-learning-databases/kddcup99-mld/kddcup.data.gz
ARCHIVE = RemoteFileMetadata(
    filename='kddcup99_data',
    url='https://ndownloader.figshare.com/files/5976045',
    checksum=('3b6c942aa0356c0ca35b7b595a26c89d'
              '343652c9db428893e7494f837b274292'))

# The original data can be found at:
# https://archive.ics.uci.edu/ml/machine-learning-databases/kddcup99-mld/kddcup.data_10_percent.gz
ARCHIVE_10_PERCENT = RemoteFileMetadata(
    filename='kddcup99_10_data',
    url='https://ndownloader.figshare.com/files/5976042',
    checksum=('8045aca0d84e70e622d1148d7df78249'
              '6f6333bf6eb979a1b0837c42a9fd9561'))

logger = logging.getLogger(__name__)


def fetch_kddcup99(subset=None, data_home=None, shuffle=False,
                   random_state=None,
                   percent10=True, download_if_missing=True, return_X_y=False):
    """Load the kddcup99 dataset (classification).

    Download it if necessary.

    =================   ====================================
    Classes                                               23
    Samples total                                    4898431
    Dimensionality                                        41
    Features            discrete (int) or continuous (float)
    =================   ====================================

    Read more in the :ref:`User Guide <kddcup99_dataset>`.

    .. versionadded:: 0.18

    Parameters
    ----------
    subset : None, 'SA', 'SF', 'http', 'smtp'
        To return the corresponding classical subsets of kddcup 99.
        If None, return the entire kddcup 99 dataset.

    data_home : string, optional
        Specify another download and cache folder for the datasets. By default
        all scikit-learn data is stored in '~/scikit_learn_data' subfolders.
        .. versionadded:: 0.19

    shuffle : bool, default=False
        Whether to shuffle dataset.

    random_state : int, RandomState instance or None (default)
        Determines random number generation for dataset shuffling and for
        selection of abnormal samples if `subset='SA'`. Pass an int for
        reproducible output across multiple function calls.
        See :term:`Glossary <random_state>`.

    percent10 : bool, default=True
        Whether to load only 10 percent of the data.

    download_if_missing : bool, default=True
        If False, raise a IOError if the data is not locally available
        instead of trying to download the data from the source site.

    return_X_y : boolean, default=False.
        If True, returns ``(data, target)`` instead of a Bunch object. See
        below for more information about the `data` and `target` object.

        .. versionadded:: 0.20

    Returns
    -------
    data : Bunch
        Dictionary-like object, the interesting attributes are:
         - 'data', the data to learn.
         - 'target', the regression target for each sample.
         - 'DESCR', a description of the dataset.

    (data, target) : tuple if ``return_X_y`` is True

        .. versionadded:: 0.20
    """
    data_home = get_data_home(data_home=data_home)
    kddcup99 = _fetch_brute_kddcup99(data_home=data_home,
                                     percent10=percent10,
                                     download_if_missing=download_if_missing)

    data = kddcup99.data
    target = kddcup99.target

    if subset == 'SA':
        s = target == b'normal.'
        t = np.logical_not(s)
        normal_samples = data[s, :]
        normal_targets = target[s]
        abnormal_samples = data[t, :]
        abnormal_targets = target[t]

        n_samples_abnormal = abnormal_samples.shape[0]
        # selected abnormal samples:
        random_state = check_random_state(random_state)
        r = random_state.randint(0, n_samples_abnormal, 3377)
        abnormal_samples = abnormal_samples[r]
        abnormal_targets = abnormal_targets[r]

        data = np.r_[normal_samples, abnormal_samples]
        target = np.r_[normal_targets, abnormal_targets]

    if subset == 'SF' or subset == 'http' or subset == 'smtp':
        # select all samples with positive logged_in attribute:
        s = data[:, 11] == 1
        data = np.c_[data[s, :11], data[s, 12:]]
        target = target[s]

        data[:, 0] = np.log((data[:, 0] + 0.1).astype(float, copy=False))
        data[:, 4] = np.log((data[:, 4] + 0.1).astype(float, copy=False))
        data[:, 5] = np.log((data[:, 5] + 0.1).astype(float, copy=False))

        if subset == 'http':
            s = data[:, 2] == b'http'
            data = data[s]
            target = target[s]
            data = np.c_[data[:, 0], data[:, 4], data[:, 5]]

        if subset == 'smtp':
            s = data[:, 2] == b'smtp'
            data = data[s]
            target = target[s]
            data = np.c_[data[:, 0], data[:, 4], data[:, 5]]

        if subset == 'SF':
            data = np.c_[data[:, 0], data[:, 2], data[:, 4], data[:, 5]]

    if shuffle:
        data, target = shuffle_method(data, target, random_state=random_state)

    module_path = dirname(__file__)
    with open(join(module_path, 'descr', 'kddcup99.rst')) as rst_file:
        fdescr = rst_file.read()

    if return_X_y:
        return data, target

    return Bunch(data=data, target=target, DESCR=fdescr)


def _fetch_brute_kddcup99(data_home=None,
                          download_if_missing=True, percent10=True):

    """Load the kddcup99 dataset, downloading it if necessary.

    Parameters
    ----------
    data_home : string, optional
        Specify another download and cache folder for the datasets. By default
        all scikit-learn data is stored in '~/scikit_learn_data' subfolders.

    download_if_missing : boolean, default=True
        If False, raise a IOError if the data is not locally available
        instead of trying to download the data from the source site.

    percent10 : bool, default=True
        Whether to load only 10 percent of the data.

    Returns
    -------
    dataset : dict-like object with the following attributes:
        dataset.data : numpy array of shape (494021, 41)
            Each row corresponds to the 41 features in the dataset.
        dataset.target : numpy array of shape (494021,)
            Each value corresponds to one of the 21 attack types or to the
            label 'normal.'.
        dataset.DESCR : string
            Description of the kddcup99 dataset.

    """

    data_home = get_data_home(data_home=data_home)
    dir_suffix = "-py3"

    if percent10:
        kddcup_dir = join(data_home, "kddcup99_10" + dir_suffix)
        archive = ARCHIVE_10_PERCENT
    else:
        kddcup_dir = join(data_home, "kddcup99" + dir_suffix)
        archive = ARCHIVE

    samples_path = join(kddcup_dir, "samples")
    targets_path = join(kddcup_dir, "targets")
    available = exists(samples_path)

    if download_if_missing and not available:
        _mkdirp(kddcup_dir)
        logger.info("Downloading %s" % archive.url)
        _fetch_remote(archive, dirname=kddcup_dir)
        dt = [('duration', int),
              ('protocol_type', 'S4'),
              ('service', 'S11'),
              ('flag', 'S6'),
              ('src_bytes', int),
              ('dst_bytes', int),
              ('land', int),
              ('wrong_fragment', int),
              ('urgent', int),
              ('hot', int),
              ('num_failed_logins', int),
              ('logged_in', int),
              ('num_compromised', int),
              ('root_shell', int),
              ('su_attempted', int),
              ('num_root', int),
              ('num_file_creations', int),
              ('num_shells', int),
              ('num_access_files', int),
              ('num_outbound_cmds', int),
              ('is_host_login', int),
              ('is_guest_login', int),
              ('count', int),
              ('srv_count', int),
              ('serror_rate', float),
              ('srv_serror_rate', float),
              ('rerror_rate', float),
              ('srv_rerror_rate', float),
              ('same_srv_rate', float),
              ('diff_srv_rate', float),
              ('srv_diff_host_rate', float),
              ('dst_host_count', int),
              ('dst_host_srv_count', int),
              ('dst_host_same_srv_rate', float),
              ('dst_host_diff_srv_rate', float),
              ('dst_host_same_src_port_rate', float),
              ('dst_host_srv_diff_host_rate', float),
              ('dst_host_serror_rate', float),
              ('dst_host_srv_serror_rate', float),
              ('dst_host_rerror_rate', float),
              ('dst_host_srv_rerror_rate', float),
              ('labels', 'S16')]
        DT = np.dtype(dt)
        logger.debug("extracting archive")
        archive_path = join(kddcup_dir, archive.filename)
        file_ = GzipFile(filename=archive_path, mode='r')
        Xy = []
        for line in file_.readlines():
            line = line.decode()
            Xy.append(line.replace('\n', '').split(','))
        file_.close()
        logger.debug('extraction done')
        os.remove(archive_path)

        Xy = np.asarray(Xy, dtype=object)
        for j in range(42):
            Xy[:, j] = Xy[:, j].astype(DT[j])

        X = Xy[:, :-1]
        y = Xy[:, -1]
        # XXX bug when compress!=0:
        # (error: 'Incorrect data length while decompressing[...] the file
        #  could be corrupted.')

        _joblib.dump(X, samples_path, compress=0)
        _joblib.dump(y, targets_path, compress=0)
    elif not available:
        if not download_if_missing:
            raise IOError("Data not found and `download_if_missing` is False")

    try:
        X, y
    except NameError:
        X = _joblib.load(samples_path)
        y = _joblib.load(targets_path)

    return Bunch(data=X, target=y)


def _mkdirp(d):
    """Ensure directory d exists (like mkdir -p on Unix)
    No guarantee that the directory is writable.
    """
    try:
        os.makedirs(d)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
