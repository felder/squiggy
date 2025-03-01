#!/usr/bin/env node

/**
 * Copyright ©2023. The Regents of the University of California (Regents). All Rights Reserved.
 *
 * Permission to use, copy, modify, and distribute this software and its documentation
 * for educational, research, and not-for-profit purposes, without fee and without a
 * signed licensing agreement, is hereby granted, provided that the above copyright
 * notice, this paragraph and the following two paragraphs appear in all copies,
 * modifications, and distributions.
 *
 * Contact The Office of Technology Licensing, UC Berkeley, 2150 Shattuck Avenue,
 * Suite 510, Berkeley, CA 94720-1620, (510) 643-7201, otl@berkeley.edu,
 * http://ipira.berkeley.edu/industry-info for commercial licensing opportunities.
 *
 * IN NO EVENT SHALL REGENTS BE LIABLE TO ANY PARTY FOR DIRECT, INDIRECT, SPECIAL,
 * INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING LOST PROFITS, ARISING OUT OF
 * THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN IF REGENTS HAS BEEN ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 * REGENTS SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. THE
 * SOFTWARE AND ACCOMPANYING DOCUMENTATION, IF ANY, PROVIDED HEREUNDER IS PROVIDED
 * "AS IS". REGENTS HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES,
 * ENHANCEMENTS, OR MODIFICATIONS.
 */

// IMPORTANT: Compile this Typescript file with `scripts/compile_whiteboard_to_png.sh`.

const _ = require('lodash')
const fabric = require('fabric').fabric

// The amount of padding (in pixels) that should be added to whiteboards that get exported to PNG
const WHITEBOARD_PADDING = 10

/**
 * Export a whiteboard as a PNG
 *
 * @api private
 */
const init = () => {
  // Get the whiteboard elements from standard in
  getWhiteboardElements(function(whiteboardElements) {

    // Create a PNG stream for these elements
    generatePng(whiteboardElements, function(err, data, dimensions) {
      if (err) {
        console.error(err)
        process.exit(2)
      }

      // Write the PNG data out over standard out and exit the process
      data.pipe(process.stdout)
      data.on('error', function() {
        console.error(err)
        console.error('Could not write out PNG data')
        process.exit(1)
      })
      data.on('end', function() {
        writeWhiteboardData('\n' + JSON.stringify(dimensions), function() {
          process.exit(0)
        })
      })
    })
  })
}

/**
 * Write data to the stdout stream, checking return value and waiting on the 'drain'
 * event if necessary to ease backpressure.
 * @see https://nodejs.org/api/stream.html#stream_event_drain
 *
 * @param  {Buffer|String}  data               Buffer or string to write to stdout
 * @param  {Function}       callback           Standard callback function
 * @api private
 */
 const writeWhiteboardData = (data, callback) => {
  if (process.stdout.write(data)) {
    return callback()
  } else {
    process.stdout.once('drain', function() {
      process.stdout.write(data)
      return callback()
    })
  }
}

/**
 * Get the whiteboard elements that are passed in over standard in
 *
 * @param  {Function}   callback                        Standard callback function
 * @param  {Object[]}   callback.whiteboardElements     The whiteboard elements that were passed in over standard in
 * @api private
 */
const getWhiteboardElements = (callback) => {
  // By default, the standard in stream is paused. Resume it and collect all the chunks
  process.stdin.resume()
  process.stdin.setEncoding('utf8')

  let data = ''
  process.stdin.on('data', chunk => {
    data += chunk.toString()
    if (data.indexOf('\n') !== -1) {
      // Although we only expect 1 line-break to be passed in, ensure we don't end up calling the
      // callback multiple times
      process.stdin.pause()

      // Parse the collected chunks and return the whiteboard elements to the caller
      let whiteboardElements = []
      try {
        whiteboardElements = JSON.parse(data.split('\n')[0])
      } catch (err) {
        console.error(err)
        console.error('Could not parse the input JSON')
        process.exit(1)
      }

      return callback(whiteboardElements)
    }
  })
}

/**
 * Generate a PNG version of a canvas that holds the whiteboard elements
 *
 * @param  {Object[]}     whiteboardElements      The elements on the canvas
 * @param  {Function}     callback                Standard callback function
 * @param  {Object}       callback.err            An error that occurred, if any
 * @param  {Buffer}       callback.data           The PNG version of the elements on the canvas
 * @api private
 */
const generatePng = (whiteboardElements, callback) => {
  // Variables that will keep track of what the outer corners of the elements in the canvas are
  let left = Number.MAX_VALUE
  let top = Number.MAX_VALUE
  let right = Number.MIN_VALUE
  let bottom = Number.MIN_VALUE

  // A variable that will keep track of all the deserialized elements in the whiteboard
  const deserialized = []

  const render = _.after(whiteboardElements.length, function() {
    // At this point we've figured out what the left-most and right-most element is. By subtracting
    // their X-coordinates we get the desired width of the canvas. The height can be calculated in
    // a similar way by using the Y-coordinates
    let width = right - left
    let height = bottom - top

    // Neither width nor height should exceed 2048px.
    let scaleFactor = 1
    if (width > 2048 && width >= height) {
      scaleFactor = 2048 / width
    } else if (height > 2048 && height > width) {
      scaleFactor = 2048 / height
    }

    if (scaleFactor < 1) {
      // If scaling down is required, first change the canvas dimensions.
      width = width * scaleFactor
      height = height * scaleFactor
      // Next, scale and reposition each element against top left corner of the canvas.
      _.each(deserialized, function(object) {
        const element = object.element
        element.scaleX = element.scaleX * scaleFactor
        element.scaleY = element.scaleY * scaleFactor
        element.left = left + ((element.left - left) * scaleFactor)
        element.top = top + ((element.top - top) * scaleFactor)
      })
    }

    // Add a bit of padding so elements don't stick to the side
    width += (2 * WHITEBOARD_PADDING)
    height += (2 * WHITEBOARD_PADDING)

    // Create a canvas and pan it to the top-left corner
    const canvas = createCanvas(width, height)
    const pt = new fabric.Point(left - WHITEBOARD_PADDING, top - WHITEBOARD_PADDING)
    canvas.absolutePan(pt)

    // Don't render each element when it's added, rather render the entire Canvas once all elements
    // have been added. This is significantly faster
    canvas.renderOnAddRemove = false

    // Once all elements have been added to the canvas, restore
    // the layer order and convert to PNG
    const finishRender = _.after(deserialized.length, function() {
      canvas.renderAll()

      const dimensions = {
        'width': width,
        'height': height
      }

      // Convert the canvas to a PNG file and return the data
      //stream = canvas.nodeCanvas.toBuffer(function(err, buff) {
      const stream = canvas.createPNGStream()
      return callback(null, stream, dimensions)
    })

    // Add each element to the canvas
    const sorted = _.sortBy(deserialized, object => object.zIndex)
    _.each(sorted, function(object) {
      canvas.add(object.element)
      finishRender()
    })
  })

  _.each(whiteboardElements, function(whiteboardElement) {
    // Canvas doesn't seem to deal terribly well with text elements that specify a prioritized list
    // of font family names. It seems that the only way to render custom fonts is to only specify one
    if (whiteboardElement.fontFamily) {
      whiteboardElement.fontFamily = 'HelveticaNeue-Light'
    }

    // Deserialize the element, get its boundary and check how large
    // the canvas should be to display the element entirely
    deserializeElement(whiteboardElement, function(deserializedElement) {
      const bound = deserializedElement.getBoundingRect()

      left = Math.min(left, bound.left)
      top = Math.min(top, bound.top)
      right = Math.max(right, bound.left + bound.width)
      bottom = Math.max(bottom, bound.top + bound.height)

      // Retain a reference to the deserialized elements. This allows for moving each element
      // to the right z-index once all elements have been added to the canvas
      deserialized.push({element: deserializedElement, zIndex: whiteboardElement.zIndex})

      render()
    })
  })
}

/* Fabric utilities */

// Ensure that the horizontal and vertical origins of objects are set to center
fabric.Object.prototype.originX = fabric.Object.prototype.originY = 'center'

/**
 * Create a Fabric.JS canvas instance. The `HelveticaNeue-Light` font will be pre-loaded
 *
 * @param  {Number}     width     The width of the desired Canvas instance
 * @param  {Number}     height    The height of the desired Canvas instance
 * @return {Canvas}               A Fabric.JS canvas instance
 * @api private
 */
const createCanvas = (width, height) => {
  // Add the Helvetica Neueu font so text elements can be rendered correctly
  const fontPath = __dirname + '/HelveticaNeueuLight.ttf'
  const font = new fabric.nodeCanvas.Font('HelveticaNeue-Light', fontPath)

  // Create a canvas of the desired dimensions
  const canvas = new fabric.Canvas(null, {width: width, height: height})
  canvas.backgroundColor = '#fff'

  canvas.contextContainer.addFont(font)
  return canvas
}

/**
 * Convert a serialized Fabric.js canvas element to a proper Fabric.js canvas element
 *
 * @param  {Object}         element           The serialized Fabric.js canvas element to deserialize
 * @param  {Function}       callback          Standard callback function
 * @param  {Object}         callback.element  The deserialized Fabric.js canvas element
 * @api private
 */
const deserializeElement = (element, callback) => {
  // Extract the type from the serialized element
  const type = fabric.util.string.camelize(fabric.util.string.capitalize(element.type))
  fabric[type].fromObject(element, callback)
}

// Initialize the script
init()
