// Punycode shim for React Native / Metro environment
module.exports = {
  toASCII: function(input) { return input; },
  toUnicode: function(input) { return input; },
  encode: function(input) { return input; },
  decode: function(input) { return input; },
  version: '2.3.1',
  ucs2: {
    decode: function(string) {
      const output = [];
      let counter = 0;
      const length = string.length;
      while (counter < length) {
        const value = string.charCodeAt(counter++);
        if (value >= 0xD800 && value <= 0xDBFF && counter < length) {
          const extra = string.charCodeAt(counter++);
          if ((extra & 0xFC00) === 0xDC00) {
            output.push(((value & 0x3FF) << 10) + (extra & 0x3FF) + 0x10000);
          } else {
            output.push(value);
            counter--;
          }
        } else {
          output.push(value);
        }
      }
      return output;
    },
    encode: function(array) {
      return String.fromCodePoint.apply(String, array);
    }
  }
};
