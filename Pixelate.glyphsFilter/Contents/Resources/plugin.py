# encoding: utf-8

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
	def start(self):
		
		# Set default value
		Glyphs.registerDefault("com.mekkablue.Pixelate.pixelComponentName", "pixel")
		Glyphs.registerDefault("com.mekkablue.Pixelate.pixelRasterWidth", "50")
		Glyphs.registerDefault("com.mekkablue.Pixelate.resetWidths", True)
		
		# Set value of text field
		self.pixelComponentNameField.setStringValue_( Glyphs.defaults["com.mekkablue.Pixelate.pixelComponentName"] )
		self.pixelRasterWidthField.setStringValue_( Glyphs.defaults["com.mekkablue.Pixelate.pixelRasterWidth"] )
		self.resetWidthsField.setState_( int(bool(Glyphs.defaults["com.mekkablue.Pixelate.resetWidths"])) )
		
		# Set focus to text field
		self.pixelComponentNameField.becomeFirstResponder()
		
	# Actions triggered by UI:
	@objc.IBAction
	def setPixelComponentName_( self, sender ):
		Glyphs.defaults['com.mekkablue.Pixelate.pixelComponentName'] = sender.stringValue()
		self.update()
		
	@objc.IBAction
	def setPixelRasterWidth_( self, sender ):
		Glyphs.defaults['com.mekkablue.Pixelate.pixelRasterWidth'] = sender.intValue()
		self.update()
		
	@objc.IBAction
	def setResetWidths_( self, sender ):
		Glyphs.defaults['com.mekkablue.Pixelate.resetWidths'] = sender.state()
		self.update()
	
	# Actual filter
	def filter(self, thisLayer, inEditView, customParameters):
		
		# Called on font export, get values from customParameters
		if customParameters.has_key('snapwidth'):
			widthsShouldBeReset = customParameters['snapwidth']
		if customParameters.has_key('grid'):
			pixelRasterWidth = customParameters['grid']
		if customParameters.has_key('component'):
			pixelNameEntered = customParameters['component']
		
		# Called through UI, use stored values
		else:
			widthsShouldBeReset = bool(Glyphs.defaults['com.mekkablue.Pixelate.resetWidths'])
			pixelRasterWidth = int(Glyphs.defaults['com.mekkablue.Pixelate.pixelRasterWidth'])
			pixelNameEntered = str(Glyphs.defaults['com.mekkablue.Pixelate.pixelComponentName'])
		
		try:
			thisGlyph = thisLayer.parent
			thisFont = thisGlyph.parent
			pixelRasterWidth = max(5,abs(pixelRasterWidth)) # safety precaution
			
			if thisFont and thisGlyph.name != pixelNameEntered:
				pixel = thisFont.glyphs[ pixelNameEntered ]
				
				# remove existing pixel components to avoid endless iteration:
				for i in range(len(thisLayer.components))[::-1]:
					if thisLayer.components[i].componentName == pixelNameEntered:
						del thisLayer.components[i]
				
				if len(thisLayer.paths) > 0 or len(thisLayer.components) > 0:
					# get all possible pixel positions within layer bounds:
					thisLayerBezierPath = thisLayer.copyDecomposedLayer().bezierPath # necessary for containsPoint_() function
					layerBounds = thisLayer.bounds
					xStart = int(round( layerBounds.origin.x / pixelRasterWidth ))
					yStart = int(round( layerBounds.origin.y / pixelRasterWidth ))
					xIterations = int(round( layerBounds.size.width / pixelRasterWidth ))
					yIterations = int(round( layerBounds.size.height / pixelRasterWidth ))
					pixelCount = 0

					if inEditView:
						# move current layer to background and clean foreground:
						thisLayer.background.clear()
						thisLayer.swapForegroundWithBackground()
					else:
						thisLayer.clear()
					
					# snap width to pixel grid:
					if widthsShouldBeReset:
						originalWidth = thisLayer.width
						pixelatedWidth = round( originalWidth / pixelRasterWidth ) * pixelRasterWidth
						thisLayer.setWidth_( pixelatedWidth )
				
					# add pixels:
					for x in range(xStart, xStart + xIterations):
						for y in range( yStart, yStart + yIterations):
							# if the pixel center is black, insert a pixel component here:
							pixelCenter = NSPoint( (x+0.5) * pixelRasterWidth, (y+0.5) * pixelRasterWidth )
							if thisLayerBezierPath.containsPoint_( pixelCenter ):
								pixelCount += 1
								pixelComponent = GSComponent( pixel, NSPoint( x * pixelRasterWidth, y * pixelRasterWidth ) )
								pixelComponent.alignment = -1 # prevent automatic alignment
								thisLayer.addComponent_( pixelComponent )
					
					if not inEditView:
						thisLayer.decomposeComponents()
						thisLayer.removeOverlap()

					# print "%s: added %i pixels to layer '%s'%s." % ( thisGlyph.name, pixelCount, thisLayer.name )
			
		except Exception, e:
			import traceback
			t = str(traceback.format_exc())
			errorMsg = "Pixelate Error: %s\n%s" % (e, t)
			self.logToConsole( errorMsg )

			# brings macro window to front and reports error:
			if inEditView:
				Glyphs.showMacroWindow()
				print errorMsg
			
	
	def generateCustomParameter( self ):
		return "%s; grid:%s; component:%s; snapwidth:%s" % (
			self.__class__.__name__, 
			Glyphs.defaults["com.mekkablue.Pixelate.pixelRasterWidth"],
			Glyphs.defaults["com.mekkablue.Pixelate.pixelComponentName"],
			Glyphs.defaults["com.mekkablue.Pixelate.resetWidths"],
			)
	
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
