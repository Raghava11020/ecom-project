# E-commerce Data Generator

This project generates sample CSV files for an e-commerce database according to the specified schema.

## Files Generated

1. **customers.csv** - Customer information (100 records)
2. **products.csv** - Product catalog (50 records)
3. **orders.csv** - Customer orders (200 records)
4. **order_items.csv** - Order line items
5. **payments.csv** - Payment transactions

## Schema

### customers.csv
- `customer_id` (integer, unique)
- `customer_name` (text)
- `email` (text)
- `phone number` (text)
- `city` (text)
- `country` (text)

### products.csv
- `product_id` (integer, unique)
- `product_name` (text)
- `category` (text)
- `price` (real)

### orders.csv
- `order_id` (integer, unique)
- `customer_id` (integer, references customers.customer_id)
- `order_date` (date)
- `status` (text)

### order_items.csv
- `item_id` (integer, unique)
- `order_id` (integer, references orders.order_id)
- `product_id` (integer, references products.product_id)
- `quantity` (integer)
- `price` (real)

### payments.csv
- `payment_id` (integer, unique)
- `amount` (real)
- `order_id` (integer, references orders.order_id)
- `payment_method` (text)
- `payment_date` (date)

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Step 1: Generate CSV Files

Run the data generation script:

```bash
python generatedata.py
```

The script will generate all 5 CSV files in the current directory with dates between 2006 and 2007.

### Step 2: Import to SQLite Database

After generating the CSV files, import them into a SQLite database:

```bash
python ingest_to_sqlite.py
```

This will create a SQLite database file named `ecommerce.db` with all the data imported from the CSV files.

## Database Schema

The SQLite database (`ecommerce.db`) contains the following tables:
- `customers` - Customer information
- `products` - Product catalog
- `orders` - Customer orders
- `order_items` - Order line items
- `payments` - Payment transactions

All tables include proper foreign key relationships to maintain referential integrity.

## Configuration

You can modify the following variables in `generatedata.py` to adjust the data volume:
- `NUM_CUSTOMERS` - Number of customers to generate
- `NUM_PRODUCTS` - Number of products to generate
- `NUM_ORDERS` - Number of orders to generate
- `MIN_ITEMS_PER_ORDER` / `MAX_ITEMS_PER_ORDER` - Range of items per order

