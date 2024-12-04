class Cart {
    constructor() {
        this.items = [];
        this.total = 0;
    }

    addItem(service) {
        this.items.push(service);
        this.calculateTotal();
        this.updateUI();
    }

    removeItem(serviceId) {
        this.items = this.items.filter(item => item.id !== serviceId);
        this.calculateTotal();
        this.updateUI();
    }

    calculateTotal() {
        this.total = this.items.reduce((sum, item) => sum + item.price, 0);
    }

    updateUI() {
        // Update cart display
        const cartElement = document.getElementById('cart');
        // Update UI logic here
    }
}

