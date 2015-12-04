import os
import random
from lib import mriutil

from lib.images import Images
from core.toad.generictask import GenericTask
__author__ = "Mathieu Desrosiers"
__copyright__ = "Copyright (C) 2014, TOAD"
__credits__ = ["Mathieu Desrosiers"]


class Atlas(GenericTask):


    def __init__(self, subject):
        """initialisation methods. Please leave as is"""

        GenericTask.__init__(self, subject, 'parcellation', 'qa')


    def implement(self):

        self.__createImageFromAtlas("template_brodmann", self.get("brodmann"))
        self.__createImageFromAtlas("template_aal2", self.get("aal2"))
        self.__createImageFromAtlas("template_networks7", self.get("networks7"))


    def __createImageFromAtlas(self, source, target):
        """
            Create a area map base on a source name
        Args:
            source: template name as specify into config.cfg
            target: output file name

        Returns:
            A brodmann area images

        """
        tmpImage = 'tmp_{0:.6g}.mgz'.format(random.randint(0,999999))
        template = os.path.join(self.toadDir, "templates", "mri", self.get(source))

        self.info("Set SUBJECTS_DIR to {}".format(self.parcellationDir))
        os.environ["SUBJECTS_DIR"] = self.parcellationDir

        cmd = "mri_vol2vol --mov {} --targ $FREESURFER_HOME/subjects/fsaverage/mri/T1.mgz" \
              " --o {} --regheader --interp nearest".format(template, tmpImage)
        self.launchCommand(cmd)

        cmd =  "mri_vol2vol --mov $SUBJECTS_DIR/{0}/mri/norm.mgz --targ {1} --s {0} " \
               " --m3z talairach.m3z --o {2} --interp nearest --inv-morph".format(self.get('parcellation', 'id'), tmpImage, target)
        self.launchCommand(cmd)
        return mriutil.convertAndRestride(target, target, self.get('preparation', 'stride_orientation'))


    def meetRequirement(self):
        """Validate if all requirements have been met prior to launch the task

        Returns:
            True if all requirement are meet, False otherwise
        """
        return Images((self.getParcellationImage('anat', 'freesurfer'), 'anatomical'))


    def isDirty(self):
        return Images( (self.getImage('brodmann'), 'brodmann atlas'),
                  (self.getImage('aal2'), 'buckner atlas'),
                  (self.getImage('networks7'), 'seven networks atlas'))


    def qaSupplier(self):
        anat = self.getParcellationImage('anat', 'freesurfer')

        brodmann = self.getImage('brodmann')
        aal2 = self.getImage('aal2')
        networks7 = self.getImage('networks7')
        brodmannPng = self.buildName(brodmann, None, 'png')
        aal2Png = self.buildName(aal2, None, 'png')
        networks7Png = self.buildName(networks7, None, 'png')
        self.slicerPng(anat, brodmannPng, segOverlay=brodmann, boundaries=brodmann)
        self.slicerPng(anat, aal2Png, segOverlay=aal2, boundaries=aal2)
        self.slicerPng(anat, networks7Png, segOverlay=networks7, boundaries=networks7)

        qaImages = Images(
            (brodmannPng, 'Brodmann segmentation from freesurfer'),
            (aal2Png, 'Aal2 segmentation from freesurfer'),
            (networks7Png, 'Seven networks segmentation from freesurfer'))

        return qaImages