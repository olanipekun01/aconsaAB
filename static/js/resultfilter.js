// JavaScript logic for managing state and actions
const sessionSelect = document.getElementById('session-select');
const semesterSelect = document.getElementById('semester-select');
const viewResultBtn = document.getElementById('view-result-btn');

function updateButtonState() {
  viewResultBtn.disabled = !(sessionSelect.value && semesterSelect.value);
}

sessionSelect.addEventListener('change', updateButtonState);
semesterSelect.addEventListener('change', updateButtonState);

viewResultBtn.addEventListener('click', () => {
  const selectedSession = sessionSelect.value;
  const selectedSemester = semesterSelect.value;

  if (selectedSession && selectedSemester) {
    alert(`Viewing results for ${selectedSession}, ${selectedSemester}`);
  }
});