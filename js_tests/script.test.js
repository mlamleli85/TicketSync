/**
 * @jest-environment jsdom
 *
 * Automated tests for static/js/script.js
 * Run with:  npm test
 */
const {
  getCounterState,
  setUpCharacterCounter,
  autoDismissSuccessAlerts,
  SUCCESS_ALERT_DELAY_MS
} = require("../static/js/script.js");

describe("getCounterState", () => {
  test("reports how many characters are still needed", () => {
    expect(getCounterState("Too short", 20)).toEqual({
      message: "9 characters - 11 more needed",
      tooShort: true
    });
  });

  test("ignores leading and trailing spaces", () => {
    expect(getCounterState("   abc   ", 5).message)
      .toBe("3 characters - 2 more needed");
  });

  test("reports only the length once the minimum is reached", () => {
    const text = "a".repeat(20);
    expect(getCounterState(text, 20)).toEqual({
      message: "20 characters",
      tooShort: false
    });
  });

  test("handles an empty description", () => {
    expect(getCounterState("", 20).message)
      .toBe("0 characters - 20 more needed");
  });
});

describe("setUpCharacterCounter", () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <textarea data-min-length="20"></textarea>
      <div id="char-counter"></div>`;
  });

  test("shows the counter as soon as the page loads", () => {
    expect(setUpCharacterCounter(document)).toBe(true);
    const counter = document.getElementById("char-counter");
    expect(counter.textContent).toBe("0 characters - 20 more needed");
    expect(counter.classList.contains("text-danger")).toBe(true);
  });

  test("updates as the user types and removes the warning colour", () => {
    setUpCharacterCounter(document);
    const textarea = document.querySelector("textarea");
    textarea.value = "The printer shows a paper jam error.";
    textarea.dispatchEvent(new Event("input"));
    const counter = document.getElementById("char-counter");
    expect(counter.textContent).toBe("36 characters");
    expect(counter.classList.contains("text-danger")).toBe(false);
  });

  test("does nothing on pages without a description box", () => {
    document.body.innerHTML = "<p>No form here</p>";
    expect(setUpCharacterCounter(document)).toBe(false);
  });
});

describe("autoDismissSuccessAlerts", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    document.body.innerHTML = `
      <div class="alert alert-success">Saved</div>
      <div class="alert alert-info">Logged out</div>
      <div class="alert alert-danger">Error</div>`;
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test("closes success and info messages after the delay", () => {
    const closeAlert = jest.fn();
    const count = autoDismissSuccessAlerts(document, closeAlert);
    expect(count).toBe(2);
    expect(closeAlert).not.toHaveBeenCalled();
    jest.advanceTimersByTime(SUCCESS_ALERT_DELAY_MS);
    expect(closeAlert).toHaveBeenCalledTimes(2);
  });

  test("never closes error messages", () => {
    const closeAlert = jest.fn();
    autoDismissSuccessAlerts(document, closeAlert);
    jest.advanceTimersByTime(SUCCESS_ALERT_DELAY_MS * 2);
    const closed = closeAlert.mock.calls.map((call) => call[0].textContent);
    expect(closed).not.toContain("Error");
  });
});
