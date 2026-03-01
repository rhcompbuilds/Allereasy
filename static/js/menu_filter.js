// static/js/menu_filter.js

function buildFilterUrl(baseUrl) {
    const filterCheckboxes = document.querySelectorAll('.allergen-checkbox');

    // IDs of UNCHECKED allergens = those we want to exclude
    const excludedIds = Array.from(filterCheckboxes)
        .filter(cb => !cb.checked)
        .map(cb => cb.value)
        .join(',');

    const url = new URL(baseUrl, window.location.origin);
    const params = new URLSearchParams();

    // Subcategory (if one is selected)
    if (typeof selectedSubcategorySlug !== 'undefined' && selectedSubcategorySlug) {
        params.set('subcategory', selectedSubcategorySlug);
    }

    // Excluded allergens
    params.set('excluded_allergens', excludedIds);

    url.search = params.toString();

    return { url: url.toString(), excludedIds };
}

async function fetchDishes(baseUrl) {
    const dishListContainer = document.getElementById('dish-list-container');
    if (!dishListContainer) return;

    const { url, excludedIds } = buildFilterUrl(baseUrl);

    // Simple loading state
    dishListContainer.classList.add('is-loading');

    try {
        const response = await fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        if (!response.ok) {
            throw new Error('Network error while fetching dishes');
        }

        const html = await response.text();
        dishListContainer.innerHTML = html;

        // Keep the URL in sync so filters can be shared/bookmarked
        const current = new URL(window.location.href);
        current.searchParams.set('excluded_allergens', excludedIds);

        if (typeof selectedSubcategorySlug !== 'undefined' && selectedSubcategorySlug) {
            current.searchParams.set('subcategory', selectedSubcategorySlug);
        } else {
            current.searchParams.delete('subcategory');
        }

        window.history.replaceState({}, '', current.toString());
    } catch (err) {
        console.error(err);
        dishListContainer.innerHTML = `
            <div class="no-dishes-found">
                <p>Sorry, something went wrong while updating the menu.</p>
                <p>Please try changing your allergen filters again.</p>
            </div>
        `;
    } finally {
        dishListContainer.classList.remove('is-loading');
    }
}

// Initialise listeners after DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (typeof menuDetailBaseUrl === 'undefined') return;

    const dishListContainer = document.getElementById('dish-list-container');
    if (!dishListContainer) return;

    const filterCheckboxes = document.querySelectorAll('.allergen-checkbox');
    filterCheckboxes.forEach((checkbox) => {
        checkbox.addEventListener('change', () => fetchDishes(menuDetailBaseUrl));
    });
});
