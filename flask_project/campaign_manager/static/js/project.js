function deleteRequest() {
  var popup = document.getElementById("delete-pop");
  var background = document.getElementById("delete-background");
  if (popup.style.display == "none" && background.style.display == "none") {
    popup.style.display = "inline-table";
    background.style.display = "block";
  } else {
    popup.style.display = "none";
    background.style.display = "none";
  }
}
