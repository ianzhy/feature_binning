// copy from https://github.com/spreadtheweb/multi-range-slider
// and modified by !an

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

function roundToStep(value, step) {
  v = Math.round(value/step)*step;
  if(step<1 && String(v).split(".")[1] && String(v).split(".")[1].length>10){
    v = Number(v.toFixed(String(step).split(".")[1].length));
  }
  return v;
}


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
      values: [25,75],
      step: 0.1,
      min: 0,
      max: 1000,
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
    this.transform();

    this.container = this.initContainer(selector);

    this.jump = this.container.offsetWidth / Math.ceil((this.allProps.max - this.allProps.min) / this.allProps.step);
    this.rail = this.initRail();

    this.tooltip = this.initTooltip();
    this.initPoints(this.allProps.values);

    this.documentMouseupHandler = this.documentMouseupHandler.bind(this);
    this.documentMouseMoveHandler = this.documentMouseMoveHandler.bind(this);
    this.selectedPointIndex = -1;
    this.changeHandlers = [];
    this.mouseOverHandlers = [];
    this.mouseOutHandlers = [];
    return this;
  }
  /**
   * Draw all elements with initial positions
   */ 




  _createClass(RangeSlider, [{
    key: "transform",
    value: function transform() {
      
      if(this.allProps.xtype==="log"){
        this.transformFunc = Math.log;
        this.transformFuncInv = a=>roundToStep(Math.exp(a),this.allProps.step);
      }else if(this.allProps.xtype==="exp"){
        this.transformFunc = Math.exp;
        this.transformFuncInv = a=>roundToStep(Math.log(a),this.allProps.step);
      }else{                        // fall back to linear
        this.transformFunc = a=>a;
        this.transformFuncInv = a=>roundToStep(a,this.allProps.step);
      }

      this.allProps.min = this.transformFunc(this.allProps.min);
      this.allProps.max = this.transformFunc(this.allProps.max);
      this.allProps.values = this.allProps.values.map(this.transformFunc);

    }
  
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
      this.container.appendChild(rail);
      return rail;
    }
    /**
     * Initialize all tracks (equal to number of points - 1)
     * @param  {number} count
     */


  }, {
    key: "initPoints",
    value: function initPoints(values) {
      this.points = [];
      
      for (var i = 0; i < values.length; i++) {
        this.addPoint(values[i]);
      }

    }
    /**
     * Initialize single track at specific index position
     * @param  {number} index
     */

  },{  
    key: "addPoint",
    value: function addPoint(value) {
      var _this55 = this;
      var point = document.createElement("span");
      point.value_pct = ((value - _this55.allProps.min) / (_this55.allProps.max - _this55.allProps.min) * 100).toFixed(1);
      point.value = value;
      point.classList.add("range-slider__point");
      point.style.width = _this55.allProps.pointRadius * 2 + "px";
      point.style.height = _this55.allProps.pointRadius * 2 + "px";
      point.style.left = "".concat(point.value_pct, "%");
      var pointColors = _this55.allProps.colors.points;
      
      _this55.points.push(point);
      _this55.container.appendChild(point);
      point.get_index = function() {return _this55.points.indexOf(point)};
      
      point.style.background = Array.isArray(pointColors) ? pointColors[index] || pointColors[pointColors.length - 1] : pointColors;
      point.addEventListener("mousedown", function (e) {
        return _this55.pointClickHandler(e, this.get_index());
      });
      point.addEventListener("mouseover", function (e) {
        return _this55.pointMouseoverHandler(e, this.get_index());
      });
      point.addEventListener("mouseout", function (e) {
        return _this55.pointMouseOutHandler(e, this.get_index());
      });

      point.addEventListener("dblclick", function (e) {
        return _this55.pointDblclickHandler(e, this.get_index());
      });

      return point;
    }
  
  
  },{
    key: "removePoint",
    value: function removePoint(index) {
      this.points[index].remove();
      this.points.splice(index, 1);
    }

  }, {
    key: "initTooltip",
    value: function initTooltip() {
      var tooltip = document.createElement("span");
      tooltip.classList.add("range-slider__tooltip");
      tooltip.style.fontSize = this.allProps.pointRadius + "px";
      this.container.appendChild(tooltip);
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
        point.style.left = "".concat(point.value_pct, "%");
      });

      this.tooltip.style.left = "".concat(this.points[this.selectedPointIndex].value_pct,"%");
      this.tooltip.textContent = this.transformFuncInv(this.points[this.selectedPointIndex].value);
    }
    /**
     * Redraw on rail click
     * @param  {Event} e
     */
  }, {
    key: "railClickHandler",
    value: function railClickHandler(e) {
      var percent = this.getPercentageX(e.pageX);
      var value = this.getAbsoluteX(e.pageX);

      this.tooltip.style.transform = "translate(-50%, -60%) scale(1)";
      this.tooltip.style.left = "".concat(percent,"%");
      this.tooltip.textContent = this.transformFuncInv(this.transformFuncInv(value));
    }
    /**
     * Find the closest possible point position fro current mouse position
     * in order to move the point
     * @param  {number} mousePoisition
     */
  
  },{  
    key: "railDblclickHandler",
    value: function railDblclickHandler(e) {
      _this66 = this;;
      var percent = _this66.getPercentageX(e.pageX);
      var value = _this66.getAbsoluteX(e.pageX);
      console.log(value);
      console.log(percent);
      _this66.addPoint(value);

      _this66.changeHandlers.forEach(function (func) {
        return func(_this66.allProps.values);
      });
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
      this.points[this.selectedPointIndex].value_pct = this.getPercentageX(e.pageX);
      this.points[this.selectedPointIndex].value = this.getAbsoluteX(e.pageX);
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
      let _this = this;
      var transparentColor = RangeSlider.addTransparencyToColor(_this.points[index].style.backgroundColor, 16);

      if (_this.selectedPointIndex < 0) {
        _this.points[index].style.boxShadow = "0px 0px 0px ".concat(Math.floor(_this.allProps.pointRadius / 1.5), "px ").concat(transparentColor);
      }

      _this.tooltip.style.transform = "translate(-50%, -60%) scale(1)";
      _this.tooltip.style.left = "".concat(_this.points[index].value_pct + "%");
      _this.tooltip.textContent = _this.transformFuncInv(_this.points[index].value);
      // console.log("mouse over on point: "+index);
      // console.log(_this.getValueByIndex(index));
      _this.mouseOverHandlers.forEach(function (func) {
        return func(index,_this.getValueByIndex(index));
      });
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
      let _this=this;
      if (_this.selectedPointIndex < 0) {
        _this.points[index].style.boxShadow = "none";
        _this.tooltip.style.transform = "translate(-50%, -60%) scale(0)";
        // console.log("mouse out on point: "+index);
        _this.mouseOutHandlers.forEach(function (func) {
          return func(index,_this.getValueByIndex(index));
        });
      }
    }
    /**
     * Get mouse position relatively from containers left position on the page
     */

  },{
    key: "pointDblclickHandler",
    value: function pointDblclickHandler(e, index) {
      _this22 = this;
      console.log(this.points[index].value_pct);
      console.log(this.points[index].value);
      this.removePoint(index);
      _this22.changeHandlers.forEach(function (func) {
        return func(_this22.allProps.values);
      });
    }
  }, {
    key: "getMouseRelativePosition",
    value: function getMouseRelativePosition(pageX) {
      return pageX - this.container.offsetLeft;
    }
    /**
     * Register onChange callback to call it on slider move end passing all the present values
     */

  },{
    key: "getAbsoluteX",
    value: function getAbsoluteX(pageX) {
      return (pageX - this.container.offsetLeft) / this.container.offsetWidth * (this.allProps.max - this.allProps.min) + this.allProps.min;
    }

  },{
    key: "getPercentageX",
    value: function getPercentageX(pageX) {
      return ((pageX - this.container.offsetLeft)/this.container.offsetWidth * 100 ).toFixed(1);
    }

  },{
    key: "getValues",
    value: function getValues() {
      _this = this;
      return this.points.map(function (point) {
        return _this.transformFuncInv(point.value);
      });
    }

  },{
    key: "getValueByIndex",
    value: function getValueByIndex(index) {
      _this = this;
      return _this.transformFuncInv(_this.points[index].value);
    }


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