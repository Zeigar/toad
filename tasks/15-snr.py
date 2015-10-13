# -*- coding: utf-8 -*-
import numpy
import nibabel
import scipy.ndimage.morphology

from core.toad.generictask import GenericTask
from lib.images import Images
from lib import mriutil


__author__ = "Christophe Bedetti"
__copyright__ = "Copyright (C) 2014, TOAD"
__credits__ = ["Christophe Bedetti"]


class Snr(GenericTask):


    def __init__(self, subject):
        GenericTask.__init__(self, subject, 'preparation', 'correction', 'denoising', 'masking', 'qa')

    def implement(self):

        #Noise mask computation
        brainMask = self.getCorrectionImage('mask', 'corrected')

        noiseMask = mriutil.computeNoiseMask(brainMask, self.buildName(brainMask, 'noisemask'))

        #Voxel Size of native dwi
        dwiNative = self.getPreparationImage('dwi')
        voxelSize = mriutil.getMriVoxelSize(dwiNative)

        #Corpus Callosum masks
        ccMask = self.getMaskingImage('aparc_aseg', ['253','mask'])
        ccMaskDownsample = self.buildName(ccMask, 'downsample')
        cmdString = "mri_convert -voxsize {} -rl {} --input_volume {} --output_volume {}"
        cmd = cmdString.format(" ".join(voxelSize), brainMask, ccMask, ccMaskDownsample)
        self.launchCommand(cmd)


    def __noiseAnalysis(self, dwi, noiseMask, ccMask, qaImages, description):
        """

        """
        snrPng = self.buildName(dwi, 'snr', 'png')
        histPng = self.buildName(dwi, 'hist', 'png')
        self.noiseAnalysis(dwi, noiseMask, ccMask, snrPng, histPng)
        qaImages.extend(Images(
            (snrPng, '{} DWI image : SNR for each volume'.format(description)),
            (histPng, '{} DWI image : noise histogram'.format(description)),
            ))
        return qaImages


    def isIgnore(self):
        return  self.get("ignore")


    def meetRequirement(self):
        return Images(
            (self.getPreparationImage('dwi'), 'diffusion weighted'),
            (self.getCorrectionImage('mask', 'corrected'), 'brain mask'),
            (self.getMaskingImage('aparc_aseg', ['253','mask']), 'Corpus Callusum mask from masking task'),
            (self.getCorrectionImage('b0', 'corrected'), 'B0')
            )


    def isDirty(self):
        return Images(
            (self.getImage('mask', ['corrected', 'noisemask']), 'Noise mask'),
            (self.getImage('aparc_aseg', ['253', 'mask', 'downsample']), 'Corpus callosum downsample'),
            )


    def qaSupplier(self):
        """Create and supply images for the report generated by qa task

        """
        qaImages = Images()

        #Get images
        dwiNative = self.getPreparationImage('dwi')
        dwiCorrected = self.getCorrectionImage('dwi', 'corrected')
        dwiDenoised = self.getDenoisingImage('dwi', 'denoise')
        noiseMask = self.getImage('mask', ['corrected', 'noisemask'])
        ccMask = self.getImage('aparc_aseg', ['253', 'mask', 'downsample'])
        b0 = self.getCorrectionImage('b0', 'corrected')

        #Build qa images
        tags = (
            (dwiNative, 'Native'),
            (dwiCorrected, 'Corrected'),
            (dwiDenoised, 'denoised'),
            )
        for dwi, description in tags:
            if dwi:
                qaImages = self.__noiseAnalysis(dwi, noiseMask, ccMask, qaImages, description)

        #Build qa masks images
        tags = (
            (noiseMask, 'Noise mask'),
            (ccMask, 'Corpus callosum mask'),
            )
        for mask, description in tags:
            maskPng = self.buildName(mask, None, 'png')
            self.slicerPng(b0, maskPng, maskOverlay=mask, boundaries=mask)
            qaImages.extend(Images((maskPng, description)))

        return qaImages
