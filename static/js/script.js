/* TicketSync front-end behaviour */

const SUCCESS_ALERT_DELAY_MS = 5000;

/**
 * Build the text shown under the ticket description.
 * Returns the message and whether the minimum length is still unmet.
 */
function getCounterState(text, minLength) {
  const length = text.trim().length;
  if (length < minLength) {
    return {
      message: length + " characters - " + (minLength - length) +
        " more needed",
      tooShort: true
    };
  }
  return {
    message: length + " characters",
    tooShort: false
  };
}

/**
 * Show a live character count under the ticket description,
 * and how many more characters are needed to reach the minimum.
 */
function setUpCharacterCounter(root) {
  const textarea = root.querySelector("textarea[data-min-length]");
  const counter = root.getElementById("char-counter");
  if (!textarea || !counter) {
    return false;
  }

  const minLength = parseInt(textarea.dataset.minLength, 10);

  function updateCounter() {
    const state = getCounterState(textarea.value, minLength);
    counter.textContent = state.message;
    counter.classList.toggle("text-danger", state.tooShort);
  }

  textarea.addEventListener("input", updateCounter);
  updateCounter();
  return true;
}

/**
 * Close success and info messages automatically after a delay.
 * Error and warning messages stay until the user closes them.
 * `closeAlert` is passed in so the behaviour can be tested.
 */
function autoDismissSuccessAlerts(root, closeAlert) {
  const alerts = root.querySelectorAll(".alert-success, .alert-info");
  alerts.forEach(function (alertElement) {
    setTimeout(function () {
      closeAlert(alertElement);
    }, SUCCESS_ALERT_DELAY_MS);
  });
  return alerts.length;
}

/* Close an alert with Bootstrap's fade-out animation */
function closeWithBootstrap(alertElement) {
  bootstrap.Alert.getOrCreateInstance(alertElement).close();
}

if (typeof document !== "undefined" && typeof bootstrap !== "undefined") {
  document.addEventListener("DOMContentLoaded", function () {
    autoDismissSuccessAlerts(document, closeWithBootstrap);
    setUpCharacterCounter(document);
  });
}

/* Export for the Jest tests; ignored by the browser */
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    getCounterState,
    setUpCharacterCounter,
    autoDismissSuccessAlerts,
    SUCCESS_ALERT_DELAY_MS
  };
}
