// ========================================
// BOOK SELECTION — MAX 5, MIN 3
// ========================================

const MAX_BOOKS = 5;
const MIN_BOOKS = 3;

const cards = document.querySelectorAll(".book-card");

cards.forEach(card => {

    const button = card.querySelector(".select-btn");
    const checkbox = card.querySelector("input[name='selected_books']");

    if (!button || !checkbox) return;

    button.addEventListener("click", () => {

        // IF ALREADY SELECTED — ALLOW DESELECT ALWAYS
        if (checkbox.checked) {

            checkbox.checked = false;
            card.classList.remove("selected");
            button.innerText = "Select";
            return;

        }

        // IF NOT SELECTED — CHECK MAX LIMIT
        const currentlySelected = document.querySelectorAll(
            "input[name='selected_books']:checked"
        );

        if (currentlySelected.length >= MAX_BOOKS) {

            alert(
                "You can select a maximum of " + MAX_BOOKS + " books. " +
                "Please deselect a book before choosing another."
            );
            return;

        }

        // SELECT THIS CARD
        checkbox.checked = true;
        card.classList.add("selected");
        button.innerText = "Selected ✓";

    });

});


// ========================================
// BOOK FORM SUBMIT VALIDATION — MIN 3
// ========================================

const form = document.getElementById("onboardingForm");

if (form) {

    form.addEventListener("submit", (e) => {

        const checked = document.querySelectorAll(
            "input[name='selected_books']:checked"
        );

        if (checked.length < MIN_BOOKS) {

            e.preventDefault();

            alert(
                "Please select at least " + MIN_BOOKS +
                " books before continuing, or skip for now."
            );

        }

    });

}


// ========================================
// MOOD SELECTION VALIDATION — MIN 2, MAX 3
// ========================================

const moodCheckboxes = document.querySelectorAll(
    "input[name='moods']"
);

const moodForm = document.getElementById("moodForm");

if (moodCheckboxes.length > 0) {

    moodCheckboxes.forEach(checkbox => {

        checkbox.addEventListener("change", () => {

            const checked = document.querySelectorAll(
                "input[name='moods']:checked"
            );

            // ENFORCE MAXIMUM 3
            if (checked.length > 3) {

                checkbox.checked = false;

                alert("You can select a maximum of 3 moods.");

            }

        });

    });

}


// ========================================
// MOOD FORM SUBMIT VALIDATION
// ========================================

if (moodForm && moodCheckboxes.length > 0) {

    moodForm.addEventListener("submit", (e) => {

        const checked = document.querySelectorAll(
            "input[name='moods']:checked"
        );

        if (checked.length < 2) {

            e.preventDefault();

            alert("Please select at least 2 moods before continuing.");

        }

        if (checked.length > 3) {

            e.preventDefault();

            alert("Please select a maximum of 3 moods.");

        }

    });

}