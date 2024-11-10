// Save original methods in case they exist natively
const nativeMethods = {
    arrayFrom: Array.from,
    isArray: Array.isArray,
    fill: Array.prototype.fill,
    filter: Array.prototype.filter,
    find: Array.prototype.find,
    findIndex: Array.prototype.findIndex,
    forEach: Array.prototype.forEach,
    map: Array.prototype.map,
    some: Array.prototype.some
  };
  
  // Modern implementations of array methods
  const modernArrayMethods = {
    from(arrayLike, mapFn, thisArg) {
      return nativeMethods.arrayFrom.call(Array, arrayLike, mapFn, thisArg);
    },
    
    isArray(arr) {
      return nativeMethods.isArray.call(Array, arr);
    },
    
    fill(value, start, end) {
      return nativeMethods.fill.call(this, value, start, end);
    },
    
    filter(callback, thisArg) {
      return nativeMethods.filter.call(this, callback, thisArg);
    },
    
    find(callback, thisArg) {
      return nativeMethods.find.call(this, callback, thisArg);
    },
    
    findIndex(callback, thisArg) {
      return nativeMethods.findIndex.call(this, callback, thisArg);
    },
    
    forEach(callback, thisArg) {
      return nativeMethods.forEach.call(this, callback, thisArg);
    },
    
    map(callback, thisArg) {
      return nativeMethods.map.call(this, callback, thisArg);
    },
    
    some(callback, thisArg) {
      return nativeMethods.some.call(this, callback, thisArg);
    }
  };
  
  // Replace polyfilled methods with native implementations
  function optimizeArrayMethods() {
    // Static methods
    Array.from = modernArrayMethods.from;
    Array.isArray = modernArrayMethods.isArray;
    
    // Prototype methods
    Array.prototype.fill = modernArrayMethods.fill;
    Array.prototype.filter = modernArrayMethods.filter;
    Array.prototype.find = modernArrayMethods.find;
    Array.prototype.findIndex = modernArrayMethods.findIndex;
    Array.prototype.forEach = modernArrayMethods.forEach;
    Array.prototype.map = modernArrayMethods.map;
    Array.prototype.some = modernArrayMethods.some;
  }
  
  // Check if browser supports these methods natively
  function checkNativeSupport() {
    return (
      typeof Array.from === 'function' &&
      typeof Array.isArray === 'function' &&
      typeof Array.prototype.fill === 'function' &&
      typeof Array.prototype.filter === 'function' &&
      typeof Array.prototype.find === 'function' &&
      typeof Array.prototype.findIndex === 'function' &&
      typeof Array.prototype.forEach === 'function' &&
      typeof Array.prototype.map === 'function' &&
      typeof Array.prototype.some === 'function'
    );
  }
  
  // Only optimize if browser has native support
  if (checkNativeSupport()) {
    optimizeArrayMethods();
  }