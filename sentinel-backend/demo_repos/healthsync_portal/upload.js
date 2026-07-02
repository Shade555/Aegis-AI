const exec = require('child_process').exec;
function processImage(filename) {
    exec("convert " + filename + " output.png"); // Command Injection
}