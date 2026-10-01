/* TicketSync front-end behaviour */

document.addEventListener("DOMContentLoaded", function () {
  autoDismissSuccessAlerts();
  setUpCharacterCounter();
});

/**
 * Close success messages automatically after 5 seconds.
 * Error and warning messages stay until the user closes them.
 */
function autoDismissSuccessAlerts() {
  const alerts = document.querySelectorAll(".alert-success, .alert-info");
  alerts.forEach(function (alertElement) {
    setTimeout(function () {
      const alert = bootstrap.Alert.getOrCreateInstance(alertElement);
      alert.close();
    }, 5000);
  });
}

/**
 * Show a live character count under the ticket description,
 * and how many more characters are needed to reach the minimum.
 */
function setUpCharacterCounter() {
  const textarea = document.querySelector("textarea[data-min-length]");
  const counter = document.getElementById("char-counter");
  if (!textarea || !counter) {
    return;
  }

  const minLength = parseInt(textarea.dataset.minLength, 10);

  function updateCounter() {
    const length = textarea.value.trim().length;
    if (length < minLength) {
      counter.textContent = length + " characters - " +
        (minLength - length) + " more needed";
      counter.classList.add("text-danger");
    } else {
      counter.textContent = length + " characters";
      counter.classList.remove("text-danger");
    }
  }

  textarea.addEventListener("input", updateCounter);
  updateCounter();
}
