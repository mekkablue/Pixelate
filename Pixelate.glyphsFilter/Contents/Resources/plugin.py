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
		# Called through UI, use stored values
		else:
			widthsShouldBeReset = bool(Glyphs.defaults['com.mekkablue.Pixelate.resetWidths'])

		if customParameters.has_key('grid'):
			pixelRasterWidth = customParameters['grid']
		else:
			pixelRasterWidth = int(Glyphs.defaults['com.mekkablue.Pixelate.pixelRasterWidth'])

		if customParameters.has_key('component'):
			pixelNameEntered = customParameters['component']
		else:
			pixelNameEntered = str(Glyphs.defaults['com.mekkablue.Pixelate.pixelComponentName'])
		
		try:
			thisGlyph = thisLayer.parent
			thisFont = thisGlyph.parent
			pixelRasterWidth = max(5,abs(pixelRasterWidth)) # safety precaution
			
			# snap width to pixel grid:
			if widthsShouldBeReset:
				originalWidth = thisLayer.width
				pixelatedWidth = round( originalWidth / pixelRasterWidth ) * pixelRasterWidth
				thisLayer.setWidth_( pixelatedWidth )
			
			# draw pixels
			if thisFont and thisGlyph.name != pixelNameEntered:
				pixel = thisFont.glyphs[ pixelNameEntered ]
				if pixel:
					
					# first, remove existing pixel components to avoid endless iteration:
					for i in range(len(thisLayer.components))[::-1]:
						if thisLayer.components[i].componentName == pixelNameEntered:
							del thisLayer.components[i]
				
					# only draw if there is a shape (left):
					if thisLayer.paths or thisLayer.components or thisLayer.background.paths:

						# determine the shape
						thisLayerBezierPath = None
						if inEditView:
							# move current layer to background and clean foreground:
							if thisLayer.paths or thisLayer.components:
								backgroundPaths = thisLayer.copyDecomposedLayer().paths.__copy__()
								thisLayer.background.clear()
								thisLayer.background.paths = backgroundPaths
								
							# alternatively, use the background from a previous iteration:
							thisLayerBezierPath = thisLayer.background.bezierPath
						else:
							# when called as custom parameter:
							thisLayerBezierPath = thisLayer.copyDecomposedLayer().bezierPath
							thisLayer.clear()
						
						# continue only if there is anything:
						if thisLayerBezierPath:
							layerBounds = thisLayer.bounds
							xStart = int(round( layerBounds.origin.x / pixelRasterWidth ))
							yStart = int(round( layerBounds.origin.y / pixelRasterWidth ))
							xIterations = int(round( layerBounds.size.width / pixelRasterWidth ))
							yIterations = int(round( layerBounds.size.height / pixelRasterWidth ))
							pixelCount = 0

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
							
							# decompose if called as parameter:
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
