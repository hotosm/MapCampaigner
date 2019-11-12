function deleteRequest() {
  const popup = document.getElementById("delete-pop");
  const background = document.getElementById("delete-background");
  if (popup.style.display == "none" && background.style.display == "none") {
    popup.style.display = "inline-table";
    background.style.display = "block";
  } else {
    popup.style.display = "none";
    background.style.display = "none";
  }
}

function confirmDelete() {
  const deleteBtn = document.getElementById("delete-btn");
  if (deleteBtn.hasAttribute("disabled")){
    deleteBtn.removeAttribute("disabled");
  } else {
   deleteBtn.setAttribute("disabled", " ");
  }
}

function executeDeletion(campaignId) {
  console.log(campaignId);
  const xhr = new XMLHttpRequest();
  const url = '/campaign/' + campaignId + '/delete';
  console.log(url);
  xhr.open("POST", url, true);
  xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
  xhr.send("");
}
