# encoding: utf-8
from __future__ import division, print_function, unicode_literals

###########################################################################################################
#
#
#	Filter with dialog Plugin
#
#	Read the docs:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/Filter%20with%20Dialog
#
#	For help on the use of Interface Builder:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates
#
#
###########################################################################################################

import objc
from GlyphsApp import *
from GlyphsApp.plugins import *

class Pixelate(FilterWithDialog):

	# Definitions of IBOutlets

	# The NSView object from the User Interface. Keep this here!
	dialog = objc.IBOutlet()

	# Text field in dialog
	pixelComponentNameField = objc.IBOutlet()
	pixelRasterWidthField = objc.IBOutlet()
	resetWidthsField = objc.IBOutlet()

	@objc.python_method
	def settings(self):
		self.menuName = Glyphs.localize({
			'en': u'Pixelate',
			'de': u'Verpixeln',
			'fr': u'Pixelliser',
			'es': u'Pixelar',
		})

		# Word on Run Button (default: Apply)
		self.actionButtonLabel = Glyphs.localize({
			'en': u'Pixelate',
			'de': u'Verpixeln',
			'fr': u'Pixelliser',
			'es': u'Pixelar',
		})

		# Load dialog from .nib (without .extension)
		self.loadNib('IBdialog', __file__)

	# On dialog show
	@objc.python_method
	def start(self):

		# Set default value
		Glyphs.registerDefault("com.mekkablue.Pixelate.pixelComponentName", "pixel")
		Glyphs.registerDefault("com.mekkablue.Pixelate.pixelRasterWidth", "50")
		Glyphs.registerDefault("com.mekkablue.Pixelate.resetWidths", True)

		# Set value of text field
		self.pixelComponentNameField.setStringValue_(Glyphs.defaults["com.mekkablue.Pixelate.pixelComponentName"])
		self.pixelRasterWidthField.setStringValue_(Glyphs.defaults["com.mekkablue.Pixelate.pixelRasterWidth"])
		self.resetWidthsField.setState_(int(bool(Glyphs.defaults["com.mekkablue.Pixelate.resetWidths"])))

		# Set focus to text field
		self.pixelComponentNameField.becomeFirstResponder()

	# Actions triggered by UI:
	@objc.IBAction
	def setPixelComponentName_(self, sender):
		Glyphs.defaults['com.mekkablue.Pixelate.pixelComponentName'] = sender.stringValue()
		self.update()

	@objc.IBAction
	def setPixelRasterWidth_(self, sender):
		Glyphs.defaults['com.mekkablue.Pixelate.pixelRasterWidth'] = sender.intValue()
		self.update()

	@objc.IBAction
	def setResetWidths_(self, sender):
		Glyphs.defaults['com.mekkablue.Pixelate.resetWidths'] = sender.state()
		self.update()

	# Actual filter
	@objc.python_method
	def filter(self, thisLayer, inEditView, customParameters):

		# Called on font export, get values from customParameters
		if 'snapwidth' in customParameters:
			widthsShouldBeReset = bool(customParameters['snapwidth'])
		# Called through UI, use stored values
		else:
			widthsShouldBeReset = Glyphs.boolDefaults['com.mekkablue.Pixelate.resetWidths']

		if 'grid' in customParameters:
			pixelRasterWidth = int(customParameters['grid'])
		else:
			pixelRasterWidth = Glyphs.intDefaults['com.mekkablue.Pixelate.pixelRasterWidth']

		if 'component' in customParameters:
			pixelNameEntered = customParameters['component'].strip()
		else:
			pixelNameEntered = Glyphs.defaults['com.mekkablue.Pixelate.pixelComponentName'].strip()

		try:
			thisGlyph = thisLayer.parent
			thisFont = thisGlyph.parent
			pixelRasterWidth = max(5, abs(pixelRasterWidth)) # safety precaution

			if not thisFont:
				print("⚠️ Pixelate Error: No font open for pixelating.")
				return

			if thisGlyph.name == pixelNameEntered:
				if inEditView:
					print("⚠️ Pixelate Error: Cannot pixelate ‘%s’ with itself." % pixelNameEntered)
				return

			pixel = thisFont.glyphs[pixelNameEntered]
			if not pixel and inEditView:
				print("⚠️ Pixelate Error: No pixel glyph named ‘%s’ found in font." % pixelNameEntered)
				return

			thisLayer.beginChanges()

			# snap width to pixel grid:
			if widthsShouldBeReset:
				originalWidth = thisLayer.width
				pixelatedWidth = round(originalWidth / pixelRasterWidth) * pixelRasterWidth
				thisLayer.width = pixelatedWidth

			# first, remove existing pixel components to avoid endless iteration:
			for i in range(len(thisLayer.shapes))[::-1]:
				component = thisLayer.shapes[i]
				if isinstance(component, GSComponent) and component.componentName == pixelNameEntered:
					del(thisLayer.shapes[i])

			# only draw if there is a shape (left):
			if thisLayer.shapes or thisLayer.background.shapes:
				# determine the shape
				thisLayerBezierPath = None
				if inEditView:
					# use the background as reference
					# either from a previous iteration
					# or from the foreground > background conversion
					
					if len(thisLayer.shapes) > 0:
						thisLayer.background.shapes = thisLayer.shapes.copy()
					thisLayerBezierPath = thisLayer.background.completeBezierPath
				else:
					# when called as custom parameter:
					thisLayerBezierPath = thisLayer.completeBezierPath
				# continue only if there is anything:
				if thisLayerBezierPath is None:
					thisLayer.endChanges()
					return
				components = []

				layerBounds = thisLayerBezierPath.bounds()
				xStart = int(round(layerBounds.origin.x / pixelRasterWidth))
				yStart = int(round(layerBounds.origin.y / pixelRasterWidth))
				xIterations = int(round(layerBounds.size.width / pixelRasterWidth))
				yIterations = int(round(layerBounds.size.height / pixelRasterWidth))
				# add pixels:
				for x in range(xStart, xStart + xIterations):
					for y in range(yStart, yStart + yIterations):
						# if the pixel center is black, insert a pixel component here:
						pixelCenter = NSPoint((x + 0.5) * pixelRasterWidth, (y + 0.5) * pixelRasterWidth)
						if thisLayerBezierPath.containsPoint_(pixelCenter):
							pixelComponent = GSComponent(pixel, NSPoint(x * pixelRasterWidth, y * pixelRasterWidth))
							pixelComponent.alignment = -1 # prevent automatic alignment
							components.append(pixelComponent)
				thisLayer.shapes = components
				# decompose if called as parameter:
				if not inEditView:
					thisLayer.decomposeComponents()
					thisLayer.removeOverlap()
			thisLayer.endChanges()

		except Exception as e:
			print("Pixelate Error:")
			import traceback
			print(traceback.format_exc())

			# brings macro window to front and reports error:
			if inEditView:
				Glyphs.showMacroWindow()
				print(errorMsg)

	@objc.python_method
	def generateCustomParameter(self):
		return "%s; grid:%s; component:%s; snapwidth:%s" % (
			self.__class__.__name__, 
			Glyphs.defaults["com.mekkablue.Pixelate.pixelRasterWidth"],
			Glyphs.defaults["com.mekkablue.Pixelate.pixelComponentName"],
			Glyphs.defaults["com.mekkablue.Pixelate.resetWidths"],
			)

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
