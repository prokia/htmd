# (c) 2015-2016 Acellera Ltd http://www.acellera.com
# All Rights Reserved
# Distributed under HTMD Software License Agreement
# No redistribution in whole or part
#
import numpy as np
from htmd.units import convert as unitconvert
import logging
logger = logging.getLogger(__name__)


class GWPCA(object):
    """ Class for calculating the globally-weighted PCA projections of a MetricData  object

    Parameters
    ----------
    data : :class:`MetricData <htmd.metricdata.MetricData>` object
        The object whose data we wish to project.

    Example
    -------
    >>> gw = GWPCA(data)
    >>> dataproj = gw.project(5)
    """

    def __init__(self, data, lag, units='frames'):
        lag = unitconvert(units, 'frames', lag, data.fstep)
        if lag == 0:
            raise RuntimeError('Lag time conversion resulted in 0 frames. Please use a larger lag-time for TICA.')
        self.data = data

        datconcat = np.concatenate(self.data.dat)
        self.weights = self._autocorrelation(datconcat, lag)

    def _autocorrelation(self, data, lag):
        # Calculate the autocorrelation of each feature
        autocorr = []
        for i in range(data.shape[1]):
            autocorr.append(np.correlate(data[0:-lag, i], data[lag:, i]))
        return np.squeeze(autocorr)

    def project(self, ndim=None):
        """ Projects the data object given to the constructor onto `ndim` dimensions

        Parameters
        ----------
        ndim : int
            The number of dimensions we want to project the data on.

        Returns
        -------
        dataTica : :class:`MetricData <htmd.metricdata.MetricData>` object
            A new :class:`MetricData <htmd.metricdata.MetricData>` object containing the projected data

        Example
        -------
        >>> gw = GWPCA(data)
        >>> dataproj = gw.project(5)
        """
        from sklearn.decomposition import IncrementalPCA
        from htmd.progress.progress import ProgressBar
        from htmd.metricdata import MetricData

        pca = IncrementalPCA(n_components=ndim, batch_size=10000)
        p = ProgressBar(len(self.data.dat))
        for d in self.data.dat:
            pca.partial_fit(d * self.weights)
            p.progress()
        p.stop()

        projdata = self.data.copy()
        p = ProgressBar(len(self.data.dat))
        for i, d in enumerate(self.data.dat):
            projdata.dat[i] = pca.transform(d * self.weights)
            p.progress()
        p.stop()

        # projdataconc = pca.fit_transform(self.weighedconcat)
        # projdata.dat = projdata.deconcatenate(projdataconc)
        return projdata