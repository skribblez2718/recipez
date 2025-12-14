document.addEventListener("DOMContentLoaded", () => {
               
    const path = window.location.pathname;
    const viewPathRegex = /^\/recipe\/[a-f0-9-]{36}$/i;
    const updatePathRegex = /^\/recipe\/update\/[a-f0-9-]{36}$/i;

    if ((path === "/recipe/create") || updatePathRegex.test(path)) {
        // --- Fix for browser validation on hidden/disabled fields ---
        const recipeForm = document.querySelector('form');
        if (recipeForm) {
            recipeForm.addEventListener('submit', function(event) {
                // Find all required fields that are hidden or disabled
                const invalids = recipeForm.querySelectorAll('[required]:not(:enabled), [required][style*="display: none"], [required][style*="visibility: hidden"]');
                invalids.forEach(field => {
                    field.removeAttribute('required');
                });
            }, true); // useCapture to run before native validation
        }

        // Add Recipe Ingredient
        const addRecipeIngredient = () => {
            addListItem("#ingredients-list", "ingredient");
        };

        // Add Recipe Step
        const addRecipeStep = () => {
            addListItem("#steps-list", "step");
        };

        /**
         * Reindex existing items from 0 upward immediately on page load
         * and attach event listeners to pre-existing delete buttons.
         */
        document.addEventListener("DOMContentLoaded", () => {
            const ingredientsList = document.querySelector("#ingredients-list");
            const stepsList = document.querySelector("#steps-list");

            if (ingredientsList) {
                resetIds(ingredientsList);
                attachDeleteListeners("#ingredients-list"); // Attach delete listeners for existing buttons
            }

            if (stepsList) {
                resetIds(stepsList);
                attachDeleteListeners("#steps-list"); // Attach delete listeners for existing buttons
            }
        });

        // Add List Item (Reusable for Ingredients and Steps)
        const addListItem = (listSelector, itemType) => {
            const listElement = document.querySelector(listSelector);
            if (!listElement) return;

            // Get the first item as a "template"
            const templateElement = listElement.children[0];
            if (!templateElement) return;

            // Determine the next index by checking the highest existing index
            const newListItemIndex = getNewListItemIndex(listElement);

            // Clone the template and update IDs/names
            const newListItem = cloneAndUpdateTemplate(templateElement, itemType, newListItemIndex);

            // Append the new item
            listElement.appendChild(newListItem);

            // Append a new delete button if it doesn't exist
            let deleteButton = newListItem.querySelector(".delete-step-btn");
            if (!deleteButton) {
                deleteButton = createDeleteButton();
                // For steps, append to the inner div container
                const innerContainer = newListItem.querySelector(".flex-1") || newListItem;
                innerContainer.appendChild(deleteButton);
            }

            // Attach the delete event listener to the new button
            deleteButton.addEventListener("click", (event) => deleteListItem(event));
        };

        // Returns an integer index, one higher than the highest existing index
        // so we consistently add new items in ascending order.
        const getNewListItemIndex = (listElement) => {
            let maxIndex = -1;
            Array.from(listElement.children).forEach((child) => {
                // Each list item has an ID like "ingredient-0" or "step-2"
                const match = child.id.match(/-(\d+)$/);
                if (match) {
                    const idx = parseInt(match[1], 10);
                    if (idx > maxIndex) {
                        maxIndex = idx;
                    }
                }
            });
            return maxIndex + 1; // Next index
        };

        // Clone the template item, clear its values, and update IDs/names
        const cloneAndUpdateTemplate = (templateElement, itemType, newIndex) => {
            // Clone the original <li> (deep clone)
            const newListItem = templateElement.cloneNode(true);

            // Update the <li>'s ID to match the new index
            newListItem.id = `${itemType}-${newIndex}`;

            // Update child elements
            const children = newListItem.querySelectorAll("[id], [name], [for], input, textarea, select");
            children.forEach((child) => {
                if (child.id) {
                    child.id = updateIdOrName(child.id, itemType, newIndex);
                }
                if (child.name) {
                    child.name = updateIdOrName(child.name, itemType, newIndex);
                }
                if (child.htmlFor) {
                    child.htmlFor = updateIdOrName(child.htmlFor, itemType, newIndex);
                }

                // Clear text/textarea/select values
                clearElementValue(child);

                // Special handling for CSRF token
                if (child.name && child.name.endsWith("csrf_token")) {
                    child.value = getCsrfToken();
                }
            });

            // Update step number display (for steps)
            const stepNumberDiv = newListItem.querySelector('.step-number');
            if (stepNumberDiv) {
                stepNumberDiv.textContent = newIndex + 1;
            }

            return newListItem;
        };

        // Look up a CSRF token from the page
        const getCsrfToken = () => {
            const csrfInput = document.querySelector("input[name$='csrf_token']");
            return csrfInput ? csrfInput.value : "";
        };

        // Clear the element's value
        const clearElementValue = (element) => {
            const tagName = element.tagName.toLowerCase();
            if (tagName === "input" && (element.type === "text" || element.type === "hidden")) {
                element.value = "";
            } else if (tagName === "textarea") {
                element.value = "";
            } else if (tagName === "select") {
                element.selectedIndex = 0;
            }
        };

        // Attach delete event listeners to all delete buttons in a list
        const attachDeleteListeners = (listSelector) => {
            const deleteButtons = document.querySelectorAll(`${listSelector} .delete-step-btn`);
            deleteButtons.forEach((button) => {
                button.addEventListener("click", (event) => deleteListItem(event));
            });
        };

        // Create a new delete button
        const createDeleteButton = () => {
            const deleteButton = document.createElement("button");
            deleteButton.className = "btn btn-danger btn-sm mt-2 delete-step-btn";
            deleteButton.type = "button";
            deleteButton.innerHTML = '<i class="fa-solid fa-trash mr-1"></i>Delete Step';
            return deleteButton;
        };

        // Convert "ingredient-3-quantity" --> "ingredient-4-quantity", etc.
        const updateIdOrName = (original, itemType, newIndex) => {
            const parts = original.split("-");
            // The second part is typically the numeric index (e.g. "0" or "1")
            if (parts.length > 1) {
                parts[1] = newIndex; // update the index
            }
            return parts.join("-");
        };

        // Delete a list item
        const deleteListItem = (event) => {
            event.preventDefault();
            const listItem = event.target.closest("li");
            const listElement = listItem.parentElement;

            listItem.remove();
            // Reindex everything from 0 again
            resetIds(listElement);
        };

        // Reindex all list items from 0 to N-1
        const resetIds = (listElement) => {
            Array.from(listElement.children).forEach((listItem, newIndex) => {
                // itemType = 'ingredient' or 'step'
                const itemType = listItem.id.split("-")[0];
                // Update the <li> ID
                listItem.id = `${itemType}-${newIndex}`;

                // Update child elements' IDs, names, and "for" attributes
                const children = listItem.querySelectorAll("[id], [name], [for]");
                children.forEach((child) => {
                    if (child.id) {
                        child.id = updateIdOrName(child.id, itemType, newIndex);
                    }
                    if (child.name) {
                        child.name = updateIdOrName(child.name, itemType, newIndex);
                    }
                    if (child.htmlFor) {
                        child.htmlFor = updateIdOrName(child.htmlFor, itemType, newIndex);
                    }
                });

                // Update step number display (for steps)
                const stepNumberDiv = listItem.querySelector('.step-number');
                if (stepNumberDiv) {
                    stepNumberDiv.textContent = newIndex + 1;
                }
            });
        };

        // --- Category Form Toggle Logic ---
        // Category form toggle variables (declare once at top scope for this block)
        const categoryFormsContainer = document.getElementById("category-forms-container");
        const categorySelectorContainer = document.getElementById("category-selector-container");
        const addCategoryFormContainer = document.getElementById("add-category-form-container");
        const showAddCategoryBtn = document.getElementById("show-add-category-btn");
        const cancelAddCategoryBtn = document.getElementById("cancel-add-category-btn");
        const categoryNameInput = document.getElementById("category-name");
        
        // Check if category-name input has a value on page load
        if (categoryNameInput && categoryNameInput.value.trim()) {
            // If value is set, hide category selector and show add category form
            if (categorySelectorContainer) {
                categorySelectorContainer.classList.add('hidden');
            }
            if (addCategoryFormContainer) {
                addCategoryFormContainer.classList.remove('hidden');
            }
        } else {
            // If no value is set, show category selector and hide add category form
            if (categorySelectorContainer) {
                categorySelectorContainer.classList.remove('hidden');
            }
            if (addCategoryFormContainer) {
                addCategoryFormContainer.classList.add('hidden');
                // Remove required from its inputs when hidden
                const inputs = addCategoryFormContainer.querySelectorAll('[required]');
                inputs.forEach(input => input.removeAttribute('required'));
            }
        }

        // Save references to all children (to ensure values are preserved when moving)
        // (Not needed if we move the nodes, but useful if logic changes)
        const saveFormState = (container) => {
            // Could be extended to save/restore values if cloning is ever needed
            return container ? container.cloneNode(true) : null;
        };

        // Note: Initial display is now handled by the category-name check above

        // Show Add Category form
        if (showAddCategoryBtn) {
            showAddCategoryBtn.addEventListener("click", function() {
                // Hide category selector, show add-category form
                if (categorySelectorContainer) {
                    categorySelectorContainer.classList.add('hidden');
                }
                if (addCategoryFormContainer) {
                    addCategoryFormContainer.classList.remove('hidden');
                }
            });
        }

        // Cancel Add Category
        if (cancelAddCategoryBtn) {
            cancelAddCategoryBtn.addEventListener("click", function() {
                // Hide add-category form, show category selector
                if (addCategoryFormContainer) {
                    addCategoryFormContainer.classList.add('hidden');
                    // Clear all input values in the hidden add-category form
                    const inputs = addCategoryFormContainer.querySelectorAll('input');
                    inputs.forEach(input => {
                        input.value = '';
                    });
                }
                if (categorySelectorContainer) {
                    categorySelectorContainer.classList.remove('hidden');
                }
            });
        }
        // --- End Category Form Toggle Logic ---

        // Event Listeners for adding Ingredients and Steps
        const addIngredientBtn = document.querySelector("#add-ingredient-btn");
        if (addIngredientBtn) {
            addIngredientBtn.addEventListener("click", addRecipeIngredient);
        }
        const addStepBtn = document.querySelector("#add-step-btn");
        if (addStepBtn) {
            addStepBtn.addEventListener("click", addRecipeStep);
        }

        // Attach delete listeners to existing ingredients and steps
        attachDeleteListeners("#ingredients-list");
        attachDeleteListeners("#steps-list");


    } else if (viewPathRegex.test(path)) {
        // Recipe view page - handle delete button and confirmation modal
        const deleteRecipeBtn = document.querySelector("#delete-recipe-btn");
        const confirmDeleteModal = document.querySelector("#confirmDeleteModal");
        const confirmDeleteBtn = document.querySelector("#confirm-delete-btn");
        const deleteRecipeForm = document.querySelector("#delete-recipe-form");

        // Only attach event listeners if all elements exist
        if (deleteRecipeBtn && confirmDeleteModal && confirmDeleteBtn && deleteRecipeForm) {
            // Custom modal implementation (replacing Bootstrap Modal)
            const showModal = () => {
                confirmDeleteModal.classList.add('show');
                confirmDeleteModal.style.display = 'block';

                // Add backdrop
                const backdrop = document.createElement('div');
                backdrop.classList.add('modal-backdrop');
                backdrop.id = 'delete-modal-backdrop';
                document.body.appendChild(backdrop);

                // Prevent body scroll
                document.body.style.overflow = 'hidden';
            };

            const hideModal = () => {
                confirmDeleteModal.classList.remove('show');
                confirmDeleteModal.style.display = 'none';

                // Remove backdrop
                const backdrop = document.getElementById('delete-modal-backdrop');
                if (backdrop) {
                    backdrop.remove();
                }

                // Restore body scroll
                document.body.style.overflow = '';
            };

            // Attach event listener to the delete button to open the modal
            deleteRecipeBtn.addEventListener("click", () => {
                showModal();
            });

            // Attach event listener to the confirm delete button to submit the form
            confirmDeleteBtn.addEventListener("click", () => {
                deleteRecipeForm.submit();
            });

            // Close modal when clicking cancel button (multiple selectors for robustness)
            const cancelBtns = confirmDeleteModal.querySelectorAll('.btn-secondary, [data-bs-dismiss="modal"], [data-dismiss="modal"]');
            cancelBtns.forEach(btn => {
                btn.addEventListener('click', hideModal);
            });

            // Close when clicking the modal backdrop
            document.addEventListener('click', (e) => {
                if (e.target.id === 'delete-modal-backdrop') {
                    hideModal();
                }
            });

            // Also close when clicking the modal overlay itself (outside content)
            confirmDeleteModal.addEventListener('click', (e) => {
                if (e.target === confirmDeleteModal) {
                    hideModal();
                }
            });
        }

        // Mobile actions menu toggle
        const mobileActionsToggle = document.querySelector("#mobile-actions-toggle");
        const mobileActionsMenu = document.querySelector("#mobile-actions-menu");
        const mobileDeleteBtn = document.querySelector("#mobile-delete-recipe-btn");
        const mobileDeleteForm = document.querySelector("#mobile-delete-recipe-form");

        if (mobileActionsToggle && mobileActionsMenu) {
            // Toggle menu on button click
            mobileActionsToggle.addEventListener("click", (e) => {
                e.stopPropagation();
                const isOpen = !mobileActionsMenu.classList.contains("hidden");

                if (isOpen) {
                    mobileActionsMenu.classList.add("hidden");
                    mobileActionsMenu.classList.remove("show");
                    mobileActionsToggle.setAttribute("aria-expanded", "false");
                } else {
                    mobileActionsMenu.classList.remove("hidden");
                    mobileActionsMenu.classList.add("show");
                    mobileActionsToggle.setAttribute("aria-expanded", "true");
                }
            });

            // Close menu when clicking outside
            document.addEventListener("click", (e) => {
                if (!mobileActionsMenu.contains(e.target) &&
                    !mobileActionsToggle.contains(e.target)) {
                    mobileActionsMenu.classList.add("hidden");
                    mobileActionsMenu.classList.remove("show");
                    mobileActionsToggle.setAttribute("aria-expanded", "false");
                }
            });

            // Handle mobile delete button - open confirmation modal
            if (mobileDeleteBtn && confirmDeleteModal && confirmDeleteBtn) {
                mobileDeleteBtn.addEventListener("click", (e) => {
                    e.preventDefault();
                    // Close the mobile menu first
                    mobileActionsMenu.classList.add("hidden");
                    mobileActionsMenu.classList.remove("show");
                    mobileActionsToggle.setAttribute("aria-expanded", "false");

                    // Show the confirmation modal
                    showModal();
                });

                // Update confirm button to use mobile form if desktop form doesn't exist
                if (!deleteRecipeForm && mobileDeleteForm) {
                    confirmDeleteBtn.addEventListener("click", () => {
                        mobileDeleteForm.submit();
                    });
                }
            }
        }
    }

    // Fraction conversion helper
    function toFraction(decimalValue) {
        const isNegative = decimalValue < 0;
        decimalValue = Math.abs(decimalValue);

        const whole = Math.floor(decimalValue);
        let fraction = decimalValue - whole;

        if (fraction === 0) {
            return (isNegative ? "-" : "") + whole.toString();
        }

        const denominatorBase = 10000;
        let numerator = Math.round(fraction * denominatorBase);

        function gcd(a, b) {
            return b ? gcd(b, a % b) : a;
        }
        const g = gcd(numerator, denominatorBase);
        numerator = numerator / g;
        const denominator = denominatorBase / g;

        let fractionStr = numerator + "/" + denominator;

        if (whole > 0) {
            fractionStr = whole + " " + fractionStr;
        }

        if (isNegative) {
            fractionStr = "-" + fractionStr;
        }
        return fractionStr;
    }

    // Grab all radio inputs
    const portionRadios = document.querySelectorAll('input[name="inlineRadioOptions"]');
    // Grab ingredient <li> items
    const ingredientItems = document.querySelectorAll("#ingredient-list li");

    function updateIngredients(multiplier) {
        ingredientItems.forEach(li => {
            const originalQty = parseFloat(li.getAttribute("data-original-quantity"));
            const measurement = li.getAttribute("data-measurement");
            const name = li.getAttribute("data-name");

            const newQty = originalQty * multiplier;
            const fractionQty = toFraction(newQty);

            li.querySelector(".ingredient-quantity").textContent = fractionQty + " ";
            li.querySelector(".ingredient-measurement").textContent = measurement + " ";
            li.querySelector(".ingredient-name").textContent = name;
        });
    }

    // Portion button active state handling
    const portionBtns = document.querySelectorAll('.portion-btn');

    // Only trigger if a radio is actually clicked
    portionRadios.forEach(radio => {
        radio.addEventListener("click", function () {
            if (this.checked) {
                const factor = parseFloat(this.value);
                updateIngredients(factor);

                // Update active state on portion buttons
                portionBtns.forEach(btn => btn.classList.remove('active'));
                const parentLabel = this.closest('.portion-btn');
                if (parentLabel) parentLabel.classList.add('active');
            }
        });
    });

    // Expandable section toggles (CSP-compliant replacement for inline onclick)
    document.querySelectorAll('.expandable-toggle').forEach(toggle => {
        toggle.addEventListener('click', function() {
            const content = this.nextElementSibling;
            const chevron = this.querySelector('.chevron-icon');
            if (content) content.classList.toggle('hidden');
            if (chevron) chevron.classList.toggle('rotate-180');
        });
    });

});