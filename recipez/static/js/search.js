// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', () => {
    // Get all recipe items - must be inside DOMContentLoaded
    const allRecipes = document.querySelectorAll(".recipe-item");

    // Prevent category edit links from triggering radio change
    document.querySelectorAll('.category-edit-link').forEach(link => {
        link.addEventListener('click', (e) => e.stopPropagation());
    });

    // Category toggle functionality
    const categoryToggle = document.getElementById('category-toggle');
    const categoryList = document.getElementById('category-list');
    const activeCategoryBadge = document.getElementById('active-category-badge');

    if (categoryToggle && categoryList) {
        categoryToggle.addEventListener('click', () => {
            const isExpanded = categoryToggle.getAttribute('aria-expanded') === 'true';
            categoryToggle.setAttribute('aria-expanded', !isExpanded);
            categoryList.classList.toggle('collapsed');
            categoryToggle.classList.toggle('expanded');
        });
    }

    // Update active category badge
    function updateActiveBadge(categoryName) {
        if (activeCategoryBadge) {
            if (categoryName === 'all' || !categoryName) {
                activeCategoryBadge.classList.add('hidden');
                activeCategoryBadge.textContent = '';
            } else {
                // Capitalize first letter of each word
                const displayName = categoryName.replace(/\b\w/g, l => l.toUpperCase());
                activeCategoryBadge.textContent = displayName;
                activeCategoryBadge.classList.remove('hidden');
            }
        }
    }

    // Filter recipes by category
    const categoryButtons = document.querySelectorAll(".btn-check");

    categoryButtons.forEach((button) => {
        button.addEventListener("change", (event) => {
            const categoryValue = event.target.value;

            // Update active state on labels
            document.querySelectorAll('.category-pill').forEach(pill => {
                pill.classList.remove('active');
            });
            event.target.parentElement.classList.add('active');

            // Update the active category badge
            updateActiveBadge(categoryValue);

            // If "all" is selected, show all recipes
            if (categoryValue === 'all') {
                allRecipes.forEach((recipe) => {
                    recipe.classList.remove("hidden");
                });
                return;
            }

            // Filter by specific category
            const categoryClass = categoryValue.replace(/ /g, "-") + "-recipe";

            allRecipes.forEach((recipe) => {
                if (recipe.classList.contains(categoryClass)) {
                    recipe.classList.remove("hidden");
                } else {
                    recipe.classList.add("hidden");
                }
            });
        });
    });

    // Filter recipes based on search term
    const itemSearch = document.querySelector("#item-search");
    if (itemSearch) {
        itemSearch.addEventListener("input", (event) => {
            const searchTerm = event.target.value.toLowerCase().trim();

            // If search is empty, show all recipes
            if (searchTerm === '') {
                allRecipes.forEach((recipe) => {
                    recipe.classList.remove("hidden");
                });
                return;
            }

            allRecipes.forEach((recipe) => {
                const recipeName = (recipe.dataset.recipeName || '').toLowerCase();
                const cardTitle = recipe.querySelector(".card-title")?.textContent?.toLowerCase() || '';

                if (recipeName.includes(searchTerm) || cardTitle.includes(searchTerm)) {
                    recipe.classList.remove("hidden");
                } else {
                    recipe.classList.add("hidden");
                }
            });
        });
    }
});
