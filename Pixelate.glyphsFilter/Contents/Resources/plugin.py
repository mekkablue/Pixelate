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
	@objc.python_method
	def filter(self, thisLayer, inEditView, customParameters):
		
		# Called on font export, get values from customParameters
		if 'snapwidth' in customParameters:
			widthsShouldBeReset = bool(customParameters['snapwidth'])
		# Called through UI, use stored values
		else:
			widthsShouldBeReset = bool(Glyphs.defaults['com.mekkablue.Pixelate.resetWidths'])

		if 'grid' in customParameters:
			pixelRasterWidth = int(customParameters['grid'])
		else:
			pixelRasterWidth = int(Glyphs.defaults['com.mekkablue.Pixelate.pixelRasterWidth'])

		if 'component' in customParameters:
			pixelNameEntered = customParameters['component'].strip()
		else:
			pixelNameEntered = Glyphs.defaults['com.mekkablue.Pixelate.pixelComponentName'].strip()
		
		try:
			thisGlyph = thisLayer.parent
			thisFont = thisGlyph.parent
			pixelRasterWidth = max(5,abs(pixelRasterWidth)) # safety precaution
			
			# snap width to pixel grid:
			if widthsShouldBeReset:
				originalWidth = thisLayer.width
				pixelatedWidth = round( originalWidth / pixelRasterWidth ) * pixelRasterWidth
				thisLayer.width = pixelatedWidth
			
			# draw pixels
			if not thisFont:
				print("⚠️ Pixelate Error: No font open for pixelating.")
			else:
				if thisGlyph.name == pixelNameEntered:
					print("⚠️ Pixelate Error: Cannot pixelate ‘%s’ with itself." % pixelNameEntered)
				else:
					pixel = thisFont.glyphs[ pixelNameEntered ]
					if not pixel and inEditView:
						print("⚠️ Pixelate Error: No pixel glyph named ‘%s’ found in font." % pixelNameEntered)
					else:
						thisLayer.beginChanges()
						# first, remove existing pixel components to avoid endless iteration:
						for i in range(len(thisLayer.components))[::-1]:
							if thisLayer.components[i].componentName == pixelNameEntered:
								del thisLayer.components[i]
				
						# only draw if there is a shape (left):
						if thisLayer.paths or thisLayer.components or thisLayer.background.paths:
							# determine the shape
							thisLayerBezierPath = None
							if inEditView:
								if thisLayer.paths or thisLayer.components:
									# move current layer to background and clean foreground:
									try:
										# GLYPHS 3
										backgroundPaths = thisLayer.copyDecomposedLayer().shapes.__copy__()
									except:
										# GLYPHS 2
										backgroundPaths = thisLayer.copyDecomposedLayer().paths.__copy__()
									
									thisLayer.background.clear()
									try:
										for backgroundPath in backgroundPaths:
											thisLayer.background.shapes.append(backgroundPath)
									except:
										thisLayer.background.paths = backgroundPaths

								# use the background as reference
								# either from a previous iteration
								# or from the foreground > background conversion above
								thisLayerBezierPath = thisLayer.background.bezierPath
							else:
								# when called as custom parameter:
								thisLayerBezierPath = thisLayer.copyDecomposedLayer().bezierPath
							
						
							# continue only if there is anything:
							if thisLayerBezierPath:
								
								# clean out foreground to make room for the pixels:
								
								components = []
								
								layerBounds = thisLayerBezierPath.bounds()
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
											components.append( pixelComponent )
								if Glyphs.versionNumber >= 3:
									thisLayer.shapes = components
								else:
									thisLayer.components = components
									thisLayer.paths = None
								
								# decompose if called as parameter:
								if not inEditView:
									thisLayer.decomposeComponents()
									thisLayer.removeOverlap()
						thisLayer.endChanges()

		except Exception as e:
			import traceback
			t = str(traceback.format_exc())
			errorMsg = "Pixelate Error: %s\n%s" % (e, t)
			self.logToConsole( errorMsg )

			# brings macro window to front and reports error:
			if inEditView:
				Glyphs.showMacroWindow()
				print(errorMsg)
			
	@objc.python_method
	def generateCustomParameter( self ):
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
