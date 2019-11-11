function deleteRequest() {
  var popup = document.getElementById("delete-pop");
  var background = document.getElementById("delete-background");
  var backgrdHeight = document.documentElement.clientHeight;
  var windowWidth = document.body.parentNode.clientWidth;
  if (popup.style.display == "none" && background.style.display == "none") {
    popup.style.display = "block";
    popup.style.top = backgrdHeight/2 - 200 + "px";
    popup.style.left = windowWidth/2 - 200 + "px";
    popup.style.background-color = rgba(147, 146, 146, 0.7);
    background.style.display = "block";
    background.style.height = backgrdHeight + "px";
  } else {
    popup.style.display = "none";
    background.style.display = "none";
  }
}
