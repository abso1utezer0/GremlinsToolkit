// eel script

function get_header_magic(path) {
    // run eel function with path as argument
    eel.get_header_magic(path)(function(ret) {
        // display result in html
        document.getElementById("magic").innerHTML = ret;
        // log result in console
        console.log('header magic: ' + ret);
        
    }
    );
}