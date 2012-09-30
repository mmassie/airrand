/*
  Copyright 2010 Google Inc.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
*/

/**
 * @fileoverview Bookmark bubble library. This is meant to be included in the
 * main JavaScript binary of a mobile web application.
 *
 * Supported browsers: iPhone / iPod / iPad Safari 3.0+
 */

var google = google || {};
google.bookmarkbubble = google.bookmarkbubble || {};


/**
 * Binds a context object to the function.
 * @param {Function} fn The function to bind to.
 * @param {Object} context The "this" object to use when the function is run.
 * @return {Function} A partially-applied form of fn.
 */
google.bind = function(fn, context) {
  return function() {
    return fn.apply(context, arguments);
  };
};


/**
 * Function used to define an abstract method in a base class. If a subclass
 * fails to override the abstract method, then an error will be thrown whenever
 * that method is invoked.
 */
google.abstractMethod = function() {
  throw Error('Unimplemented abstract method.');
};



/**
 * The bubble constructor. Instantiating an object does not cause anything to
 * be rendered yet, so if necessary you can set instance properties before
 * showing the bubble.
 * @constructor
 */
google.bookmarkbubble.Bubble = function() {
  /**
   * Handler for the scroll event. Keep a reference to it here, so it can be
   * unregistered when the bubble is destroyed.
   * @type {function()}
   * @private
   */
  this.boundScrollHandler_ = google.bind(this.setPosition, this);

  /**
   * The bubble element.
   * @type {Element}
   * @private
   */
  this.element_ = null;

  /**
   * Whether the bubble has been destroyed.
   * @type {boolean}
   * @private
   */
  this.hasBeenDestroyed_ = false;
};


/**
 * Shows the bubble if allowed. It is not allowed if:
 * - The browser is not Mobile Safari, or
 * - The user has dismissed it too often already, or
 * - The hash parameter is present in the location hash, or
 * - The application is in fullscreen mode, which means it was already loaded
 *   from a homescreen bookmark.
 * @return {boolean} True if the bubble is being shown, false if it is not
 *     allowed to show for one of the aforementioned reasons.
 */
google.bookmarkbubble.Bubble.prototype.showIfAllowed = function() {
  if (!this.isAllowedToShow_()) {
    return false;
  }

  this.show_();
  return true;
};


/**
 * Shows the bubble if allowed after loading the icon image. This method creates
 * an image element to load the image into the browser's cache before showing
 * the bubble to ensure that the image isn't blank. Use this instead of
 * showIfAllowed if the image url is http and cacheable.
 * This hack is necessary because Mobile Safari does not properly render
 * image elements with border-radius CSS.
 * @param {function()} opt_callback Closure to be called if and when the bubble
 *        actually shows.
 * @return {boolean} True if the bubble is allowed to show.
 */
google.bookmarkbubble.Bubble.prototype.showIfAllowedWhenLoaded =
    function(opt_callback) {
  if (!this.isAllowedToShow_()) {
    return false;
  }

  var self = this;
  // Attach to self to avoid garbage collection.
  var img = self.loadImg_ = document.createElement('img');
  img.src = self.getIconUrl_();
  img.onload = function() {
    if (img.complete) {
      delete self.loadImg_;
      img.onload = null;  // Break the circular reference.

      self.show_();
      opt_callback && opt_callback();
    }
  };
  img.onload();

  return true;
};


/**
 * Sets the parameter in the location hash. As it is
 * unpredictable what hash scheme is to be used, this method must be
 * implemented by the host application.
 *
 * This gets called automatically when the bubble is shown. The idea is that if
 * the user then creates a bookmark, we can later recognize on application
 * startup whether it was from a bookmark suggested with this bubble.
 *
 * NOTE: Using a hash parameter to track whether the bubble has been shown
 * conflicts with the navigation system in jQuery Mobile. If you are using that
 * library, you should implement this function to track the bubble's status in
 * a different way, e.g. using window.localStorage in HTML5.
 */
google.bookmarkbubble.Bubble.prototype.setHashParameter = google.abstractMethod;


/**
 * Whether the parameter is present in the location hash. As it is
 * unpredictable what hash scheme is to be used, this method must be
 * implemented by the host application.
 *
 * Call this method during application startup if you want to log whether the
 * application was loaded from a bookmark with the bookmark bubble promotion
 * parameter in it.
 *
 * @return {boolean} Whether the bookmark bubble parameter is present in the
 *     location hash.
 */
google.bookmarkbubble.Bubble.prototype.hasHashParameter = google.abstractMethod;


/**
 * The number of times the user must dismiss the bubble before we stop showing
 * it. This is a public property and can be changed by the host application if
 * necessary.
 * @type {number}
 */
google.bookmarkbubble.Bubble.prototype.NUMBER_OF_TIMES_TO_DISMISS = 2;


/**
 * Time in milliseconds. If the user does not dismiss the bubble, it will auto
 * destruct after this amount of time.
 * @type {number}
 */
google.bookmarkbubble.Bubble.prototype.TIME_UNTIL_AUTO_DESTRUCT = 15000;


/**
 * The prefix for keys in local storage. This is a public property and can be
 * changed by the host application if necessary.
 * @type {string}
 */
google.bookmarkbubble.Bubble.prototype.LOCAL_STORAGE_PREFIX = 'BOOKMARK_';


/**
 * The key name for the dismissed state.
 * @type {string}
 * @private
 */
google.bookmarkbubble.Bubble.prototype.DISMISSED_ = 'DISMISSED_COUNT';


/**
 * The arrow image in base64 data url format.
 * @type {string}
 * @private
 */
//google.bookmarkbubble.Bubble.prototype.IMAGE_ARROW_DATA_URL_ = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABkAAAATCAMAAABSrFY3AAABKVBMVEUAAAD///8AAAAAAAAAAAAAAAAAAADf398AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD09PQAAAAAAAAAAAC9vb0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD19fUAAAAAAAAAAAAAAADq6uoAAAAAAAAAAAC8vLzU1NTT09MAAADg4OAAAADs7OwAAAAAAAAAAAD///+cueenwerA0vC1y+3a5fb5+/3t8vr4+v3w9PuwyOy3zO3h6vfh6vjq8Pqkv+mat+fE1fHB0/Cduuifu+iuxuuivemrxOvC1PDz9vzJ2fKpwuqmwOrb5vapw+q/0vDf6ffK2vLN3PPprJISAAAAQHRSTlMAAAEGExES7FM+JhUoQSxIRwMbNfkJUgXXBE4kDQIMHSA0Tw4xIToeTSc4Chz4OyIjPfI3QD/X5OZR6zzwLSUPrm1y3gAAAQZJREFUeF5lzsVyw0AURNE3IMsgmZmZgszQZoeZOf//EYlG5Yrhbs+im4Dj7slM5wBJ4OJ+undAUr68gK/Hyb6Bcp5yBR/w8jreNeAr5Eg2XE7g6e2/0z6cGw1JQhpmHP3u5aiPPnTTkIK48Hj9Op7bD3btAXTfgUdwYjwSDCVXMbizO0O4uDY/x4kYC5SWFnfC6N1a9RCO7i2XEmQJj2mHK1Hgp9Vq3QBRl9shuBLGhcNtHexcdQCnDUoUGetxDD+H2DQNG2xh6uAWgG2/17o1EmLqYH0Xej0UjHAaFxZIV6rJ/WK1kg7QZH8HU02zmdJinKZJaDV3TVMjM5Q9yiqYpUwiMwa/1apDXTNESjsAAAAASUVORK5CYII=';
google.bookmarkbubble.Bubble.prototype.IMAGE_ARROW_DATA_URL_ = 'data:image/png;base64,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';

/**
 * The close image in base64 data url format.
 * @type {string}
 * @private
 */
// google.bookmarkbubble.Bubble.prototype.IMAGE_CLOSE_DATA_URL_ = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQBAMAAADt3eJSAAAALVBMVEXM3fm+1Pfb5/rF2fjw9f23z/aavPOhwfTp8PyTt/L3+v7T4vqMs/K7zP////+qRWzhAAAAXElEQVQIW2O4CwUM996BwVskxtOqd++2rwMyPI+ve31GD8h4Madqz2mwms5jZ/aBGS/mHIDoen3m+DowY8/hOVUgxusz+zqPg7SvPA1UxQfSvu/du0YUK2AMmDMA5H1qhVX33T8AAAAASUVORK5CYII=';
google.bookmarkbubble.Bubble.prototype.IMAGE_CLOSE_DATA_URL_ = 'data:image/png;base64,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';

/**
 * The link used to locate the application's home screen icon to display inside
 * the bubble. The default link used here is for an iPhone home screen icon
 * without gloss. If your application uses a glossy icon, change this to
 * 'apple-touch-icon'.
 * @type {string}
 * @private
 */
google.bookmarkbubble.Bubble.prototype.REL_ICON_ =
    'apple-touch-icon-precomposed';


/**
 * Regular expression for detecting an iPhone or iPod or iPad.
 * @type {!RegExp}
 * @private
 */
google.bookmarkbubble.Bubble.prototype.MOBILE_SAFARI_USERAGENT_REGEX_ =
    /iPhone|iPod|iPad/;


/**
 * Regular expression for detecting an iPad.
 * @type {!RegExp}
 * @private
 */
google.bookmarkbubble.Bubble.prototype.IPAD_USERAGENT_REGEX_ = /iPad/;


/**
 * Regular expression for extracting the iOS version. Only matches 2.0 and up.
 * @type {!RegExp}
 * @private
 */
google.bookmarkbubble.Bubble.prototype.IOS_VERSION_USERAGENT_REGEX_ =
    /OS (\d)_(\d)(?:_(\d))?/;


/**
 * Determines whether the bubble should be shown or not.
 * @return {boolean} Whether the bubble should be shown or not.
 * @private
 */
google.bookmarkbubble.Bubble.prototype.isAllowedToShow_ = function() {
  return this.isMobileSafari_() &&
      !this.hasBeenDismissedTooManyTimes_() &&
      !this.isFullscreen_() &&
      !this.hasHashParameter();
};


/**
 * Builds and shows the bubble.
 * @private
 */
google.bookmarkbubble.Bubble.prototype.show_ = function() {
  this.element_ = this.build_();

  document.body.appendChild(this.element_);
  this.element_.style.WebkitTransform =
      'translate3d(0,' + this.getHiddenYPosition_() + 'px,0)';

  this.setHashParameter();

  window.setTimeout(this.boundScrollHandler_, 1);
  window.addEventListener('scroll', this.boundScrollHandler_, false);

  // If the user does not dismiss the bubble, slide out and destroy it after
  // some time.
  window.setTimeout(google.bind(this.autoDestruct_, this),
      this.TIME_UNTIL_AUTO_DESTRUCT);
};


/**
 * Destroys the bubble by removing its DOM nodes from the document.
 */
google.bookmarkbubble.Bubble.prototype.destroy = function() {
  if (this.hasBeenDestroyed_) {
    return;
  }
  window.removeEventListener('scroll', this.boundScrollHandler_, false);
  if (this.element_ && this.element_.parentNode == document.body) {
    document.body.removeChild(this.element_);
    this.element_ = null;
  }
  this.hasBeenDestroyed_ = true;
};


/**
 * Remember that the user has dismissed the bubble once more.
 * @private
 */
google.bookmarkbubble.Bubble.prototype.rememberDismissal_ = function() {
  if (window.localStorage) {
    try {
      var key = this.LOCAL_STORAGE_PREFIX + this.DISMISSED_;
      var value = Number(window.localStorage[key]) || 0;
      window.localStorage[key] = String(value + 1);
    } catch (ex) {
      // Looks like we've hit the storage size limit. Currently we have no
      // fallback for this scenario, but we could use cookie storage instead.
      // This would increase the code bloat though.
    }
  }
};


/**
 * Whether the user has dismissed the bubble often enough that we will not
 * show it again.
 * @return {boolean} Whether the user has dismissed the bubble often enough
 *     that we will not show it again.
 * @private
 */
google.bookmarkbubble.Bubble.prototype.hasBeenDismissedTooManyTimes_ =
    function() {
  if (!window.localStorage) {
    // If we can not use localStorage to remember how many times the user has
    // dismissed the bubble, assume he has dismissed it. Otherwise we might end
    // up showing it every time the host application loads, into eternity.
    return true;
  }
  try {
    var key = this.LOCAL_STORAGE_PREFIX + this.DISMISSED_;

    // If the key has never been set, localStorage yields undefined, which
    // Number() turns into NaN. In that case we'll fall back to zero for
    // clarity's sake.
    var value = Number(window.localStorage[key]) || 0;

    return value >= this.NUMBER_OF_TIMES_TO_DISMISS;
  } catch (ex) {
    // If we got here, something is wrong with the localStorage. Make the same
    // assumption as when it does not exist at all. Exceptions should only
    // occur when setting a value (due to storage limitations) but let's be
    // extra careful.
    return true;
  }
};


/**
 * Whether the application is running in fullscreen mode.
 * @return {boolean} Whether the application is running in fullscreen mode.
 * @private
 */
google.bookmarkbubble.Bubble.prototype.isFullscreen_ = function() {
  return !!window.navigator.standalone;
};


/**
 * Whether the application is running inside Mobile Safari.
 * @return {boolean} True if the current user agent looks like Mobile Safari.
 * @private
 */
google.bookmarkbubble.Bubble.prototype.isMobileSafari_ = function() {
  return this.MOBILE_SAFARI_USERAGENT_REGEX_.test(window.navigator.userAgent);
};


/**
 * Whether the application is running on an iPad.
 * @return {boolean} True if the current user agent looks like an iPad.
 * @private
 */
google.bookmarkbubble.Bubble.prototype.isIpad_ = function() {
  return this.IPAD_USERAGENT_REGEX_.test(window.navigator.userAgent);
};


/**
 * Creates a version number from 4 integer pieces between 0 and 127 (inclusive).
 * @param {*=} opt_a The major version.
 * @param {*=} opt_b The minor version.
 * @param {*=} opt_c The revision number.
 * @param {*=} opt_d The build number.
 * @return {number} A representation of the version.
 * @private
 */
google.bookmarkbubble.Bubble.prototype.getVersion_ = function(opt_a, opt_b,
    opt_c, opt_d) {
  // We want to allow implicit conversion of any type to number while avoiding
  // compiler warnings about the type.
  return /** @type {number} */ (opt_a) << 21 |
      /** @type {number} */ (opt_b) << 14 |
      /** @type {number} */ (opt_c) << 7 |
      /** @type {number} */ (opt_d);
};


/**
 * Gets the iOS version of the device. Only works for 2.0+.
 * @return {number} The iOS version.
 * @private
 */
google.bookmarkbubble.Bubble.prototype.getIosVersion_ = function() {
  var groups = this.IOS_VERSION_USERAGENT_REGEX_.exec(
      window.navigator.userAgent) || [];
  groups.shift();
  return this.getVersion_.apply(this, groups);
};


/**
 * Positions the bubble at the bottom of the viewport using an animated
 * transition.
 */
google.bookmarkbubble.Bubble.prototype.setPosition = function() {
  this.element_.style.WebkitTransition = '-webkit-transform 0.7s ease-out';
  this.element_.style.WebkitTransform =
      'translate3d(0,' + this.getVisibleYPosition_() + 'px,0)';
};


/**
 * Destroys the bubble by removing its DOM nodes from the document, and
 * remembers that it was dismissed.
 * @private
 */
google.bookmarkbubble.Bubble.prototype.closeClickHandler_ = function() {
  this.destroy();
  this.rememberDismissal_();
};


/**
 * Gets called after a while if the user ignores the bubble.
 * @private
 */
google.bookmarkbubble.Bubble.prototype.autoDestruct_ = function() {
  if (this.hasBeenDestroyed_) {
    return;
  }
  this.element_.style.WebkitTransition = '-webkit-transform 0.7s ease-in';
  this.element_.style.WebkitTransform =
      'translate3d(0,' + this.getHiddenYPosition_() + 'px,0)';
  window.setTimeout(google.bind(this.destroy, this), 700);
};


/**
 * Gets the y offset used to show the bubble (i.e., position it on-screen).
 * @return {number} The y offset.
 * @private
 */
google.bookmarkbubble.Bubble.prototype.getVisibleYPosition_ = function() {
  return this.isIpad_() ? window.pageYOffset + 17 :
      window.pageYOffset - this.element_.offsetHeight + window.innerHeight - 17;
};


/**
 * Gets the y offset used to hide the bubble (i.e., position it off-screen).
 * @return {number} The y offset.
 * @private
 */
google.bookmarkbubble.Bubble.prototype.getHiddenYPosition_ = function() {
  return this.isIpad_() ? window.pageYOffset - this.element_.offsetHeight :
      window.pageYOffset + window.innerHeight;
};


/**
 * The url of the app's bookmark icon.
 * @type {string|undefined}
 * @private
 */
google.bookmarkbubble.Bubble.prototype.iconUrl_ = "/apple-touch-icon.png";


/**
 * Scrapes the document for a link element that specifies an Apple favicon and
 * returns the icon url. Returns an empty data url if nothing can be found.
 * @return {string} A url string.
 * @private
 */
google.bookmarkbubble.Bubble.prototype.getIconUrl_ = function() {
  if (!this.iconUrl_) {
    var link = this.getLink(this.REL_ICON_);
    if (!link || !(this.iconUrl_ = link.href)) {
      this.iconUrl_ = 'data:image/png;base64,';
    }
  }
  return this.iconUrl_;
};


/**
 * Gets the requested link tag if it exists.
 * @param {string} rel The rel attribute of the link tag to get.
 * @return {Element} The requested link tag or null.
 */
google.bookmarkbubble.Bubble.prototype.getLink = function(rel) {
  rel = rel.toLowerCase();
  var links = document.getElementsByTagName('link');
  for (var i = 0; i < links.length; ++i) {
    var currLink = /** @type {Element} */ (links[i]);
    if (currLink.getAttribute('rel').toLowerCase() == rel) {
      return currLink;
    }
  }
  return null;
};


/**
 * Creates the bubble and appends it to the document.
 * @return {Element} The bubble element.
 * @private
 */
google.bookmarkbubble.Bubble.prototype.build_ = function() {
  var bubble = document.createElement('div');
  var isIpad = this.isIpad_();

  bubble.style.position = 'absolute';
  bubble.style.zIndex = 1000;
  bubble.style.width = '100%';
  bubble.style.left = '0';
  bubble.style.top = '0';

  var bubbleInner = document.createElement('div');
  bubbleInner.style.position = 'relative';
  bubbleInner.style.width = '214px';
  bubbleInner.style.margin = isIpad ? '0 0 0 82px' : '0 auto';
  bubbleInner.style.border = '2px solid #fff';
  bubbleInner.style.padding = '20px 20px 20px 10px';
  bubbleInner.style.WebkitBorderRadius = '8px';
  bubbleInner.style.WebkitBoxShadow = '0 0 8px rgba(0, 0, 0, 0.7)';
  bubbleInner.style.WebkitBackgroundSize = '100% 8px';
  bubbleInner.style.backgroundColor = '#4F4F4F';//'#b0c8ec';
//  bubbleInner.style.background = '#cddcf3 -webkit-gradient(linear, ' +
//      'left bottom, left top, ' + isIpad ?
//          'from(#cddcf3), to(#b3caed)) no-repeat top' :
//          'from(#b3caed), to(#cddcf3)) no-repeat bottom';
  bubbleInner.style.background = '#2E3531 -webkit-gradient(linear, ' +
      'left bottom, left top, ' + isIpad ?
          'from(#2E3531), to(#4F4F4F)) no-repeat top' :
          'from(#4F4F4F), to(#2E3531)) no-repeat bottom';
  bubbleInner.style.font = '13px/17px sans-serif';
  // new by bob
  bubbleInner.style.color = '#fff';
  bubble.appendChild(bubbleInner);

  // The "Add to Home Screen" text is intended to be the exact same text
  // that is displayed in the menu of Mobile Safari.
  if (this.getIosVersion_() >= this.getVersion_(4, 2)) {
    bubbleInner.innerHTML = 'Install this web app on your phone: ' +
        'tap on the arrow and then <b>\'Add to Home Screen\'</b>';
  } else {
    bubbleInner.innerHTML = 'Install this web app on your phone: ' +
        'tap <b style="font-size:15px">+</b> and then ' +
        '<b>\'Add to Home Screen\'</b>';
  }

  var icon = document.createElement('div');
  icon.style['float'] = 'left';
  icon.style.width = '55px';
  icon.style.height = '55px';
  icon.style.margin = '-2px 7px 3px 5px';
  icon.style.background =
      '#fff url(' + this.getIconUrl_() + ') no-repeat -1px -1px';
  icon.style.WebkitBackgroundSize = '57px';
  icon.style.WebkitBorderRadius = '10px';
  icon.style.WebkitBoxShadow = '0 2px 5px rgba(0, 0, 0, 0.4)';
  bubbleInner.insertBefore(icon, bubbleInner.firstChild);

  var arrow = document.createElement('div');
  arrow.style.backgroundImage = 'url(' + this.IMAGE_ARROW_DATA_URL_ + ')';
  arrow.style.width = '25px';
  arrow.style.height = '19px';
  arrow.style.position = 'absolute';
  arrow.style.left = '111px';
  if (isIpad) {
    arrow.style.WebkitTransform = 'rotate(180deg)';
    arrow.style.top = '-19px';
  } else {
    arrow.style.bottom = '-19px';
  }
  bubbleInner.appendChild(arrow);

  var close = document.createElement('a');
  close.onclick = google.bind(this.closeClickHandler_, this);
  close.style.position = 'absolute';
  close.style.display = 'block';
  close.style.top = '-3px';
  close.style.right = '-3px';
  close.style.width = '16px';
  close.style.height = '16px';
  close.style.border = '10px solid transparent';
  close.style.background =
      'url(' + this.IMAGE_CLOSE_DATA_URL_ + ') no-repeat';
  bubbleInner.appendChild(close);

  return bubble;
};
