class ServiceManager {
    constructor() {
        this.services = [];
        this.categories = [];
        this.init();
    }

    async init() {
        await this.loadCategories();
        await this.loadServices();
        this.initializeEventListeners();
    }

    async loadCategories() {
        try {
            const response = await fetch('/api/services/categories');
            this.categories = await response.json();
            this.renderCategories();
        } catch (error) {
            console.error('Error loading categories:', error);
        }
    }

    async loadServices() {
        try {
            const response = await fetch('/api/services');
            this.services = await response.json();
            this.renderServices();
        } catch (error) {
            console.error('Error loading services:', error);
        }
    }

    renderCategories() {
        const categoryContainer = document.getElementById('service-categories');
        if (!categoryContainer) return;

        categoryContainer.innerHTML = this.categories
            .map(category => `
                <div class="category-card" data-category="${category.id}">
                    <h3>${category.name}</h3>
                    <p>${category.description}</p>
                </div>
            `).join('');
    }

    renderServices(categoryId = null) {
        const serviceContainer = document.getElementById('service-list');
        if (!serviceContainer) return;

        const filteredServices = categoryId
            ? this.services.filter(service => service.categoryId === categoryId)
            : this.services;

        serviceContainer.innerHTML = filteredServices
            .map(service => `
                <div class="service-card" data-service-id="${service.id}">
                    <h4>${service.name}</h4>
                    <p>${service.description}</p>
                    <div class="service-price">$${service.price.toFixed(2)}</div>
                    <div class="service-duration">${service.duration} mins</div>
                    <button class="btn btn-primary add-to-cart-btn">
                        Add to Cart
                    </button>
                </div>
            `).join('');
    }

    initializeEventListeners() {
        // Category filtering
        document.querySelectorAll('.category-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const categoryId = e.currentTarget.dataset.category;
                this.renderServices(categoryId);
            });
        });

        // Add to cart functionality
        document.querySelectorAll('.add-to-cart-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const serviceId = e.currentTarget
                    .closest('.service-card')
                    .dataset.serviceId;
                const service = this.services
                    .find(s => s.id === serviceId);
                cart.addItem(service);
            });
        });
    }

    // Search services
    searchServices(query) {
        const searchResults = this.services.filter(service =>
            service.name.toLowerCase().includes(query.toLowerCase()) ||
            service.description.toLowerCase().includes(query.toLowerCase())
        );
        this.renderServices(null, searchResults);
    }
}

// Initialize service manager
const serviceManager = new ServiceManager();