document.addEventListener("DOMContentLoaded", () => {
  if (!localStorage.getItem("displayName"))
    // Prompt display name
    $("#getDisplayNameModal").modal("show");

  // Add display name to local storage on display name form submission
  document.querySelector("#displayNameForm").onsubmit = function () {
    const displayName = document.querySelector("#displayNameInput").value;
    localStorage.setItem("displayName", displayName);
    $("#getDisplayNameModal").modal("hide");

    // Stop form from submitting
    return false;
  };
});
