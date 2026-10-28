// Greeting
const myName = "Luke";
console.log(`Hello, ${myName}!`);
const hobbyStorageKey = "portfolioHobbies";

// DOM Elements - Counter
const countButton = document.querySelector('.button-thing');
const countLabel = document.getElementById("count_label");

// Counter Logic
let count = 0;
if (countButton && countLabel) {
    countButton.addEventListener('click', () => {
        count++;
        countLabel.textContent = count;
    });
}

// --- Dynamic Hobby List Functionality ---
document.addEventListener("DOMContentLoaded", () => {
    const hobbyInput = document.getElementById("hobbyInput");
    const addHobbyBtn = document.getElementById("addHobbyBtn");
    const hobbyList = document.getElementById("hobbyList");

    function getHobbies() {
        return Array.from(hobbyList.querySelectorAll(".hobby-name"), item => item.textContent.trim());
    }

    function saveHobbies() {
        try {
            localStorage.setItem(hobbyStorageKey, JSON.stringify(getHobbies()));
        } catch (error) {
            console.warn("Hobbies could not be saved in this browser.");
        }
    }

    function createHobbyItem(text) {
        const item = document.createElement("li");
        item.className = "hobby-list-item";

        const label = document.createElement("span");
        label.className = "hobby-name";
        label.textContent = text;

        const removeButton = document.createElement("button");
        removeButton.type = "button";
        removeButton.className = "hobby-remove";
        removeButton.textContent = "Remove";
        removeButton.setAttribute("aria-label", `Remove ${text}`);
        removeButton.addEventListener("click", () => {
            item.remove();
            saveHobbies();
        });

        item.append(label, removeButton);
        return item;
    }

    function renderHobbies(hobbies) {
        hobbyList.replaceChildren(...hobbies.map(createHobbyItem));
    }

    function addHobby() {
        if (!hobbyInput || !hobbyList) return;
        const text = hobbyInput.value.trim();
        if (!text) return;

        hobbyList.appendChild(createHobbyItem(text));
        hobbyInput.value = "";
        hobbyInput.focus();
        saveHobbies();
    }

    if (hobbyList) {
        let hobbies = Array.from(hobbyList.children, item => item.textContent.trim()).filter(Boolean);
        try {
            const savedHobbies = JSON.parse(localStorage.getItem(hobbyStorageKey));
            if (Array.isArray(savedHobbies) && savedHobbies.every(hobby => typeof hobby === "string")) {
                hobbies = savedHobbies;
            }
        } catch (error) {
            console.warn("Saved hobbies could not be loaded.");
        }
        renderHobbies(hobbies);
        saveHobbies();
    }

    if (addHobbyBtn) addHobbyBtn.addEventListener("click", addHobby);

    if (hobbyInput) {
        hobbyInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                addHobby();
            }
        });
    }

    // Dark Mode Toggle Logic
const darkModeCheckbox = document.getElementById("darkModeCheckbox");

if (darkModeCheckbox) {
    darkModeCheckbox.addEventListener("change", () => {
        if (darkModeCheckbox.checked) {
            document.body.classList.add("dark-mode");
        } else {
            document.body.classList.remove("dark-mode");
        }
    });
}


});