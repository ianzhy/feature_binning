function _toConsumableArray(arr) { return _arrayWithoutHoles(arr) || _iterableToArray(arr) || _unsupportedIterableToArray(arr) || _nonIterableSpread(); }

function _nonIterableSpread() { throw new TypeError("Invalid attempt to spread non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }

function _unsupportedIterableToArray(o, minLen) { if (!o) return; if (typeof o === "string") return _arrayLikeToArray(o, minLen); var n = Object.prototype.toString.call(o).slice(8, -1); if (n === "Object" && o.constructor) n = o.constructor.name; if (n === "Map" || n === "Set") return Array.from(o); if (n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)) return _arrayLikeToArray(o, minLen); }

function _iterableToArray(iter) { if (typeof Symbol !== "undefined" && iter[Symbol.iterator] != null || iter["@@iterator"] != null) return Array.from(iter); }

function _arrayWithoutHoles(arr) { if (Array.isArray(arr)) return _arrayLikeToArray(arr); }

function _arrayLikeToArray(arr, len) { if (len == null || len > arr.length) len = arr.length; for (var i = 0, arr2 = new Array(len); i < len; i++) { arr2[i] = arr[i]; } return arr2; }

function ownKeys(object, enumerableOnly) { var keys = Object.keys(object); if (Object.getOwnPropertySymbols) { var symbols = Object.getOwnPropertySymbols(object); enumerableOnly && (symbols = symbols.filter(function (sym) { return Object.getOwnPropertyDescriptor(object, sym).enumerable; })), keys.push.apply(keys, symbols); } return keys; }

function _objectSpread(target) { for (var i = 1; i < arguments.length; i++) { var source = null != arguments[i] ? arguments[i] : {}; i % 2 ? ownKeys(Object(source), !0).forEach(function (key) { _defineProperty(target, key, source[key]); }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(target, Object.getOwnPropertyDescriptors(source)) : ownKeys(Object(source)).forEach(function (key) { Object.defineProperty(target, key, Object.getOwnPropertyDescriptor(source, key)); }); } return target; }

function _defineProperty(obj, key, value) { if (key in obj) { Object.defineProperty(obj, key, { value: value, enumerable: true, configurable: true, writable: true }); } else { obj[key] = value; } return obj; }

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

function _defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } }

function _createClass(Constructor, protoProps, staticProps) { if (protoProps) _defineProperties(Constructor.prototype, protoProps); if (staticProps) _defineProperties(Constructor, staticProps); Object.defineProperty(Constructor, "prototype", { writable: false }); return Constructor; }

/*
    This is a RangeSlider html component for one of my projects
    It allows to have multiple points and different ranges of values with specified steps to jumb.
    It has a easy api to customize sizes and colors of points, tracks, etc.
    It has onChange method, which receives and callback and calls it with current values
*/


var RangeSlider = /*#__PURE__*/function () {
  /**
   * Create slider
   * @param  {string} selector
   * @param  {object} props={}
   */
  function RangeSlider(selector) {
    var props = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : {};

    _classCallCheck(this, RangeSlider);

    this.defaultProps = {
      values: [25, 75],
      step: 1,
      min: 0,
      max: 100,
      colors: {
        points: "rgb(25, 118, 210)",
        // ['red', 'green', 'blue']
        rail: "rgba(25, 118, 210, 0.4)",
        tracks: "rgb(25, 118, 210)" // // ['red', 'green']

      },
      pointRadius: 15,
      railHeight: 5,
      trackHeight: 5
    };
    this.allProps = _objectSpread(_objectSpread(_objectSpread({}, this.defaultProps), props), {}, {
      values: _toConsumableArray(props.values || this.defaultProps.values),
      colors: _objectSpread(_objectSpread({}, this.defaultProps.colors), props.colors)
    });
    this.container = this.initContainer(selector);
    this.pointPositions = this.generatePointPositions();
    this.possibleValues = this.generatePossibleValues();
    this.jump = this.container.offsetWidth / Math.ceil((this.allProps.max - this.allProps.min) / this.allProps.step);
    this.rail = this.initRail();
    // this.tracks = this.initTracks(this.allProps.values.length - 1);
    this.tooltip = this.initTooltip();
    this.points = this.initPoints(this.allProps.values.length);
    this.drawScene();
    this.documentMouseupHandler = this.documentMouseupHandler.bind(this);
    this.documentMouseMoveHandler = this.documentMouseMoveHandler.bind(this);
    this.selectedPointIndex = -1;
    this.changeHandlers = [];
    return this;
  }
  /**
   * Draw all elements with initial positions
   */


  _createClass(RangeSlider, [{
    key: "drawScene",
    value: function drawScene() {
      var _this = this;

      this.container.classList.add("range-slider__container");
      this.container.appendChild(this.rail);
      this.container.appendChild(this.tooltip);
      // this.tracks.forEach(function (track) {
      //   return _this.container.appendChild(track);
      // });
      this.points.forEach(function (point) {
        return _this.container.appendChild(point);
      });
    }
  }, {
    key: "generatePointPositions",
    value: function generatePointPositions() {
      var _this2 = this;

      return this.allProps.values.map(function (value) {
        var percentage = value / _this2.allProps.max * 100;
        return Math.floor(percentage / 100 * _this2.container.offsetWidth);
      });
    }
    /**
     * Generate all values that can slider have starting from min, to max increased by step
     */

  }, {
    key: "generatePossibleValues",
    value: function generatePossibleValues() {
      var values = [];

      for (var i = this.allProps.min; i <= this.allProps.max; i += this.allProps.step) {
        values.push(Math.round(i * 100) / 100);
      }

      if (this.allProps.max % this.allProps.step > 0) {
        values.push(Math.round(this.allProps.max * 100) / 100);
      }

      return values;
    }
    /**
     * Initialize container
     * @param  {string} selector
     */

  }, {
    key: "initContainer",
    value: function initContainer(selector) {
      var container = document.querySelector(selector);
      container.classList.add("range-slider__container");
      container.style.height = this.allProps.pointRadius * 2 + "px";
      return container;
    }
    /**
     * Initialize Rail
     */

  }, {
    key: "initRail",
    value: function initRail() {
      var _this3 = this;

      var rail = document.createElement("span");
      rail.classList.add("range-slider__rail");
      rail.style.background = this.allProps.colors.rail;
      rail.style.height = this.allProps.railHeight + "px";
      rail.style.top = this.allProps.pointRadius + "px";
      // rail.addEventListener("click", function (e) {
      //   return _this3.railClickHandler(e);
      // });
      rail.addEventListener("dblclick", function (e) {
        return _this3.railDblclickHandler(e);
      });
      return rail;
    }
    /**
     * Initialize all tracks (equal to number of points - 1)
     * @param  {number} count
     */

  // }, {
  //   key: "initTracks",
  //   value: function initTracks(count) {
  //     var tracks = [];

  //     for (var i = 0; i < count; i++) {
  //       tracks.push(this.initTrack(i));
  //     }

  //     return tracks;
  //   }
  //   /**
  //    * Initialize single track at specific index position
  //    * @param  {number} index
  //    */

  // }, {
  //   key: "initTrack",
  //   value: function initTrack(index) {
  //     var _this4 = this;

  //     var track = document.createElement("span");
  //     track.classList.add("range-slider__track");
  //     var trackPointPositions = this.pointPositions.slice(index, index + 2);
  //     track.style.left = Math.min.apply(Math, _toConsumableArray(trackPointPositions)) + "px";
  //     track.style.top = this.allProps.pointRadius + "px";
  //     track.style.width = Math.max.apply(Math, _toConsumableArray(trackPointPositions)) - Math.min.apply(Math, _toConsumableArray(trackPointPositions)) + "px";
  //     track.style.height = this.allProps.trackHeight + "px";
  //     var trackColors = this.allProps.colors.tracks;
  //     track.style.background = Array.isArray(trackColors) ? trackColors[index] || trackColors[trackColors.length - 1] : trackColors;
  //     track.addEventListener("click", function (e) {
  //       return _this4.railClickHandler(e);
  //     });
  //     return track;
  //   }
  //   /**
  //    * Initialize all points (equal to number of values)
  //    * @param  {number} count
  //    */

  }, {
    key: "initPoints",
    value: function initPoints(count) {
      var points = [];
      
      for (var i = 0; i < count; i++) {
        points.push(this.initPoint(i));
      }

      return points;
    }
    /**
     * Initialize single track at specific index position
     * @param  {number} index
     */

  },{  
    key: "addPoint",
    value: function addPoint(percent) {
      var _this55 = this;
      var point = document.createElement("span");
      point.classList.add("range-slider__point");
      point.style.width = this.allProps.pointRadius * 2 + "px";
      point.style.height = this.allProps.pointRadius * 2 + "px";
      point.style.left = "".concat(50, "%");
      var pointColors = this.allProps.colors.points;
      
      this.points.push(point);
      this.container.appendChild(point);
      let index = this.points.length - 1 ;
      
      point.style.background = Array.isArray(pointColors) ? pointColors[index] || pointColors[pointColors.length - 1] : pointColors;
      point.addEventListener("mousedown", function (e) {
        return _this55.pointClickHandler(e, index);
      });
      point.addEventListener("mouseover", function (e) {
        return _this55.pointMouseoverHandler(e, index);
      });
      point.addEventListener("mouseout", function (e) {
        return _this55.pointMouseOutHandler(e, index);
      });

      point.addEventListener("dblclick", function (e) {
        return _this55.pointDblclickHandler(e, index);
      });

      return point;
    }


  }, {
    key: "initPoint",
    value: function initPoint(index) {
      var _this5 = this;

      var point = document.createElement("span");
      point.classList.add("range-slider__point");
      point.style.width = this.allProps.pointRadius * 2 + "px";
      point.style.height = this.allProps.pointRadius * 2 + "px";
      point.style.left = "".concat(this.pointPositions[index] / this.container.offsetWidth * 100, "%");
      var pointColors = this.allProps.colors.points;
      point.style.background = Array.isArray(pointColors) ? pointColors[index] || pointColors[pointColors.length - 1] : pointColors;
      point.addEventListener("mousedown", function (e) {
        return _this5.pointClickHandler(e, index);
      });
      point.addEventListener("mouseover", function (e) {
        return _this5.pointMouseoverHandler(e, index);
      });
      point.addEventListener("mouseout", function (e) {
        return _this5.pointMouseOutHandler(e, index);
      });
      return point;
    }
    /**
     * Initialize tooltip
     */

  }, {
    key: "initTooltip",
    value: function initTooltip() {
      var tooltip = document.createElement("span");
      tooltip.classList.add("range-slider__tooltip");
      tooltip.style.fontSize = this.allProps.pointRadius + "px";
      return tooltip;
    }
    /**
     * Draw points, tracks and tooltip (on rail click or on drag)
     */

  }, {
    key: "draw",
    value: function draw() {
      var _this6 = this;

      this.points.forEach(function (point, i) {
        point.style.left = "".concat(_this6.pointPositions[i] / _this6.container.offsetWidth * 100, "%");
      });
      // this.tracks.forEach(function (track, i) {
      //   var trackPointPositions = _this6.pointPositions.slice(i, i + 2);

      //   track.style.left = Math.min.apply(Math, _toConsumableArray(trackPointPositions)) + "px";
      //   track.style.width = Math.max.apply(Math, _toConsumableArray(trackPointPositions)) - Math.min.apply(Math, _toConsumableArray(trackPointPositions)) + "px";
      // });
      this.tooltip.style.left = this.pointPositions[this.selectedPointIndex] + "px";
      this.tooltip.textContent = this.allProps.values[this.selectedPointIndex];
    }
    /**
     * Redraw on rail click
     * @param  {Event} e
     */

  }, {
    key: "railClickHandler",
    value: function railClickHandler(e) {
      var newPosition = this.getMouseRelativePosition(e.pageX);
      var closestPositionIndex = this.getClosestPointIndex(newPosition);
      this.pointPositions[closestPositionIndex] = newPosition;
      this.draw();
    }
    /**
     * Find the closest possible point position fro current mouse position
     * in order to move the point
     * @param  {number} mousePoisition
     */
  
  },{  
    key: "railDblclickHandler",
    value: function railDblclickHandler(e) {
      var newPosition = this.getMouseRelativePosition(e.pageX);
      var percent = newPosition / this.container.offsetWidth * 100;
      console.log(percent);
        
    }



  }, {
    key: "getClosestPointIndex",
    value: function getClosestPointIndex(mousePoisition) {
      var shortestDistance = Infinity;
      var index = 0;

      for (var i in this.pointPositions) {
        var dist = Math.abs(mousePoisition - this.pointPositions[i]);

        if (shortestDistance > dist) {
          shortestDistance = dist;
          index = i;
        }
      }

      return index;
    }
    /**
     * Stop point moving on mouse up
     */

  }, {
    key: "documentMouseupHandler",
    value: function documentMouseupHandler() {
      var _this7 = this;

      this.changeHandlers.forEach(function (func) {
        return func(_this7.allProps.values);
      });
      this.points[this.selectedPointIndex].style.boxShadow = "none";
      this.selectedPointIndex = -1;
      this.tooltip.style.transform = "translate(-50%, -60%) scale(0)";
      document.removeEventListener("mouseup", this.documentMouseupHandler);
      document.removeEventListener("mousemove", this.documentMouseMoveHandler);
    }
    /**
     * Start point moving on mouse move
     * @param {Event} e
     */

  }, {
    key: "documentMouseMoveHandler",
    value: function documentMouseMoveHandler(e) {
      var newPoisition = this.getMouseRelativePosition(e.pageX);
      var extra = Math.floor(newPoisition % this.jump);

      if (extra > this.jump / 2) {
        newPoisition += this.jump - extra;
      } else {
        newPoisition -= extra;
      }

      if (newPoisition < 0) {
        newPoisition = 0;
      } else if (newPoisition > this.container.offsetWidth) {
        newPoisition = this.container.offsetWidth;
      }

      this.pointPositions[this.selectedPointIndex] = newPoisition;
      this.allProps.values[this.selectedPointIndex] = this.possibleValues[Math.floor(newPoisition / this.jump)];
      this.draw();
    }
    /**
     * Register document listeners on point click
     * and save clicked point index
     * @param {Event} e
     */

  }, {
    key: "pointClickHandler",
    value: function pointClickHandler(e, index) {
      e.preventDefault();
      this.selectedPointIndex = index;
      document.addEventListener("mouseup", this.documentMouseupHandler);
      document.addEventListener("mousemove", this.documentMouseMoveHandler);
    }
    /**
     * Point mouse over box shadow and tooltip displaying
     * @param {Event} e
     * @param {number} index
     */

  }, {
    key: "pointMouseoverHandler",
    value: function pointMouseoverHandler(e, index) {
      var transparentColor = RangeSlider.addTransparencyToColor(this.points[index].style.backgroundColor, 16);

      if (this.selectedPointIndex < 0) {
        this.points[index].style.boxShadow = "0px 0px 0px ".concat(Math.floor(this.allProps.pointRadius / 1.5), "px ").concat(transparentColor);
      }

      this.tooltip.style.transform = "translate(-50%, -60%) scale(1)";
      this.tooltip.style.left = this.pointPositions[index] + "px";
      this.tooltip.textContent = this.allProps.values[index];
    }
    /**
     * Add transparency for rgb, rgba or hex color
     * @param {string} color
     * @param {number} percentage
     */

  }, {
    key: "pointMouseOutHandler",
    value:
    /**
     * Hide shadow and tooltip on mouse out
     * @param {Event} e
     * @param {number} index
     */
    function pointMouseOutHandler(e, index) {
      if (this.selectedPointIndex < 0) {
        this.points[index].style.boxShadow = "none";
        this.tooltip.style.transform = "translate(-50%, -60%) scale(0)";
      }
    }
    /**
     * Get mouse position relatively from containers left position on the page
     */

  },{
    key: "pointDblclickHandler",
    value: function pointDblclickHandler(e, index) {
      console.log(this.allProps.values[index]);

    }
  }, {
    key: "getMouseRelativePosition",
    value: function getMouseRelativePosition(pageX) {
      return pageX - this.container.offsetLeft;
    }
    /**
     * Register onChange callback to call it on slider move end passing all the present values
     */

  }, {
    key: "onChange",
    value: function onChange(func) {
      if (typeof func !== "function") {
        throw new Error("Please provide function as onChange callback");
      }

      this.changeHandlers.push(func);
      return this;
    }
  }], [{
    key: "addTransparencyToColor",
    value: function addTransparencyToColor(color, percentage) {
      if (color.startsWith("rgba")) {
        return color.replace(/(\d+)(?!.*\d)/, percentage + "%");
      }

      if (color.startsWith("rgb")) {
        var newColor = color.replace(/(\))(?!.*\))/, ", ".concat(percentage, "%)"));
        return newColor.replace("rgb", "rgba");
      }

      if (color.startsWith("#")) {
        return color + percentage.toString(16);
      }

      return color;
    }
  }]);

  return RangeSlider;
}();



//# sourceURL=webpack://RangeSlider/./src/range-slider.js?