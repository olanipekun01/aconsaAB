
document.addEventListener('DOMContentLoaded', function () {
    const maxUnits = 24;  // Set the maximum allowable course units
    let totalUnits = 0;

    const courseCheckboxes = document.querySelectorAll('.course-checkbox');
    const totalUnitsDisplay = document.getElementById('totalUnits');
    const inputTotalUnits = document.getElementById('inputTotalUnits');
    const warningMessage = document.getElementById('warning');

    function updateUnits() {
        totalUnits = 0;  // Reset the total units

        // Loop through all checkboxes and sum the selected units
        courseCheckboxes.forEach(checkbox => {
            if (checkbox.checked) {
                const courseUnit = parseInt(checkbox.getAttribute('data-unit'));
                totalUnits += courseUnit;
            }
        });

        totalUnitsDisplay.textContent = totalUnits;
        inputTotalUnits.value = totalUnits;
        
        if (totalUnits > maxUnits) {
            warningMessage.style.display = 'block';
            disableUnselectedCheckboxes(true);
        } else {
            warningMessage.style.display = 'none';
            disableUnselectedCheckboxes(false);
        }
    }

    function disableUnselectedCheckboxes(disable) {
        courseCheckboxes.forEach(checkbox => {
            if (!checkbox.checked) {
                checkbox.disabled = disable;
            }
        });
    }

    courseCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateUnits);
    });

    updateUnits();
});

document.getElementById("current-date").innerText = new Date().toDateString();


function updateTotalUnits() {
    let total = 0;
    document.querySelectorAll('input.course-checkbox:checked').forEach(checkbox => {
        total += parseInt(checkbox.getAttribute('data-unit'));
    });
    document.getElementById('totalUnit').value = total;
}

function toggleDependentCourses() {
    // Reset all checkboxes to enabled
    document.querySelectorAll('input.course-checkbox').forEach(checkbox => {
        checkbox.disabled = false;
    });

    // Disable dependent courses for each selected prerequisite
    document.querySelectorAll('input.course-checkbox:checked').forEach(checked => {
        const courseId = checked.value;
        // Find courses that list this course as a prerequisite
        document.querySelectorAll(`tr[data-prereq-ids*="${courseId}"]`).forEach(row => {
            const checkbox = row.querySelector('input.course-checkbox');
            if (checkbox) {
                checkbox.disabled = true;
                checkbox.checked = false; // Uncheck if previously selected
            };
        });
    });

    // Update total units after disabling
    updateTotalUnits();
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    toggleDependentCourses();
});