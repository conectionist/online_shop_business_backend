# Frontend Guide: Payment Types and Enhanced Payment Methods

## Overview

The payment system has been enhanced to support **payment types** and **business payment details**. This allows admins to configure payment methods with specific types (e.g., Revolut, Bank Transfer) and store business payment information (where payments are received), which can then be displayed to customers during checkout.

## Key Concepts

### Payment Types
Payment types are predefined categories of payment methods (e.g., Cash, Card, Revolut, Bank Transfer). They provide:
- **Structured categorization** of payment methods
- **Business payment details** storage (where the business receives payments)
- **Display hints** for frontend apps (what information to show to customers)

### Payment Methods
Each payment method now includes:
- `payment_type_id`: Links to a payment type (0=custom, 1=cash, 2=physical_card, 3=online_card, 4=revolut, 5=bank_transfer)
- `required_data`: JSON object containing **business payment details** (where payments are received)
- `required_fields_schema`: Schema definition for displaying payment information to customers

**Important**: `required_data` contains **business payment information** (where they receive money), NOT customer input fields.

## API Endpoints

### Get All Payment Types
```http
GET /api/v1/payment-types/
```

**Response:**
```json
[
  {
    "id": 0,
    "name": "custom",
    "friendly_name": "nespecificat"
  },
  {
    "id": 1,
    "name": "cash",
    "friendly_name": "Numerar"
  },
  {
    "id": 4,
    "name": "revolut",
    "friendly_name": "Transfer Revolut"
  },
  {
    "id": 5,
    "name": "bank_transfer",
    "friendly_name": "Transfer bancar"
  }
]
```

### Get Payment Method (Updated Response)
```http
GET /api/v1/modalitati-plata/{id}
```

**Response:**
```json
{
  "id": 1,
  "name": "revolut_payment",
  "description": "Plată prin Revolut",
  "payment_type_id": 4,
  "required_data": {
    "phone_number": "0740123456"
  },
  "required_fields_schema": {
    "phone_number": {
      "label": "Număr de telefon",
      "type": "tel",
      "required": true,
      "validation": "phone",
      "description": "Număr de telefon Revolut al afacerii (unde se primesc plățile)"
    }
  }
}
```

## Frontend Implementation Guide

### 1. Displaying Payment Methods to Customers

When showing payment options during checkout, use `required_fields_schema` to display business payment information:

```javascript
// Example: Displaying Revolut payment method
function PaymentMethodCard({ paymentMethod }) {
  const { required_fields_schema, required_data, payment_type_id } = paymentMethod;
  
  // Display business payment details based on payment type
  if (payment_type_id === 4) { // Revolut
    return (
      <div className="payment-option">
        <h3>{paymentMethod.description}</h3>
        <p>Trimiteți plata la:</p>
        <p className="payment-detail">
          📱 {required_fields_schema.phone_number.label}: {required_data.phone_number}
        </p>
      </div>
    );
  }
  
  if (payment_type_id === 5) { // Bank Transfer
    return (
      <div className="payment-option">
        <h3>{paymentMethod.description}</h3>
        <p>Trimiteți plata la:</p>
        <p className="payment-detail">
          🏦 {required_fields_schema.iban.label}: {required_data.iban}
        </p>
        <p className="payment-detail">
          👤 {required_fields_schema.recipient_name.label}: {required_data.recipient_name}
        </p>
      </div>
    );
  }
  
  // For cash, card, etc. - no additional details needed
  return (
    <div className="payment-option">
      <h3>{paymentMethod.description}</h3>
    </div>
  );
}
```

### 2. Admin: Creating Payment Methods

When admins create a payment method, they must:
1. Select a payment type
2. Provide business payment details based on the selected type

```javascript
// Example: Admin form for creating Revolut payment method
async function createRevolutPaymentMethod(formData) {
  const payload = {
    name: formData.name,
    description: formData.description,
    payment_type_id: 4, // Revolut
    required_data: {
      phone_number: formData.businessPhoneNumber // Business's Revolut number
    }
  };
  
  const response = await fetch('/api/v1/modalitati-plata/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${adminToken}`
    },
    body: JSON.stringify(payload)
  });
  
  return response.json();
}
```

```javascript
// Example: Admin form for creating Bank Transfer payment method
async function createBankTransferPaymentMethod(formData) {
  const payload = {
    name: formData.name,
    description: formData.description,
    payment_type_id: 5, // Bank Transfer
    required_data: {
      iban: formData.businessIBAN, // Business's IBAN
      recipient_name: formData.businessAccountName // Business's account holder name
    }
  };
  
  const response = await fetch('/api/v1/modalitati-plata/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${adminToken}`
    },
    body: JSON.stringify(payload)
  });
  
  return response.json();
}
```

### 3. Admin: Payment Type Dropdown

Use the payment types endpoint to populate a dropdown for admins:

```javascript
// Fetch payment types for admin dropdown
async function getPaymentTypes() {
  const response = await fetch('/api/v1/payment-types/');
  const types = await response.json();
  
  // Use friendly_name for display, id for value
  return types.map(type => ({
    value: type.id,
    label: type.friendly_name
  }));
}

// Usage in admin form
function PaymentMethodForm() {
  const [paymentTypes, setPaymentTypes] = useState([]);
  
  useEffect(() => {
    getPaymentTypes().then(setPaymentTypes);
  }, []);
  
  return (
    <select name="payment_type_id">
      {paymentTypes.map(type => (
        <option key={type.value} value={type.value}>
          {type.label}
        </option>
      ))}
    </select>
  );
}
```

### 4. Dynamic Form Fields Based on Payment Type

Use `required_fields_schema` to dynamically render form fields when admins create/edit payment methods:

```javascript
function PaymentMethodForm({ paymentTypeId, formData, setFormData }) {
  const [schema, setSchema] = useState(null);
  
  // Fetch schema when payment type changes
  useEffect(() => {
    if (paymentTypeId) {
      // Get payment method to see schema (or fetch from endpoint)
      fetch(`/api/v1/modalitati-plata/`)
        .then(res => res.json())
        .then(methods => {
          // Find a method with same payment_type_id to get schema
          const example = methods.find(m => m.payment_type_id === paymentTypeId);
          if (example) {
            setSchema(example.required_fields_schema);
          }
        });
    }
  }, [paymentTypeId]);
  
  if (!schema) return null;
  
  return (
    <div>
      {Object.entries(schema).map(([fieldName, fieldSchema]) => (
        <div key={fieldName}>
          <label>{fieldSchema.label}</label>
          <input
            type={fieldSchema.type}
            value={formData.required_data?.[fieldName] || ''}
            onChange={(e) => setFormData({
              ...formData,
              required_data: {
                ...formData.required_data,
                [fieldName]: e.target.value
              }
            })}
            placeholder={fieldSchema.description}
          />
          <small>{fieldSchema.description}</small>
        </div>
      ))}
    </div>
  );
}
```

### 5. Customer Checkout Flow

**Important**: Customers do NOT need to provide any payment information. They only select a payment method:

```javascript
// Customer checkout - just select payment method
function CheckoutForm({ orderData, setOrderData }) {
  const [paymentMethods, setPaymentMethods] = useState([]);
  
  useEffect(() => {
    fetch('/api/v1/modalitati-plata/')
      .then(res => res.json())
      .then(setPaymentMethods);
  }, []);
  
  return (
    <form onSubmit={handleSubmit}>
      {/* Other order fields... */}
      
      <div className="payment-methods">
        <h3>Selectați metoda de plată</h3>
        {paymentMethods.map(method => (
          <label key={method.id}>
            <input
              type="radio"
              name="payment_method_id"
              value={method.id}
              checked={orderData.payment_method_id === method.id}
              onChange={(e) => setOrderData({
                ...orderData,
                payment_method_id: parseInt(e.target.value)
              })}
            />
            <PaymentMethodCard paymentMethod={method} />
          </label>
        ))}
      </div>
      
      <button type="submit">Plasează comanda</button>
    </form>
  );
}
```

## Payment Type Constants

For reference, here are the payment type IDs:

| ID | Name | Friendly Name |
|----|------|---------------|
| 0 | custom | nespecificat |
| 1 | cash | Numerar |
| 2 | physical_card | Plata cu cardul |
| 3 | online_card | Plata cu card online |
| 4 | revolut | Transfer Revolut |
| 5 | bank_transfer | Transfer bancar |

## Validation Rules

### When Creating/Updating Payment Methods (Admin Only)

- **Revolut** (`payment_type_id: 4`): Must have `phone_number` in `required_data`
- **Bank Transfer** (`payment_type_id: 5`): Must have both `iban` and `recipient_name` in `required_data`
- **Cash, Card types**: No `required_data` needed (should be `null` or empty object)

### When Creating Orders (Customer)

- **No validation** of payment type or `required_data`
- Only validates that the payment method exists
- Customer just selects `payment_method_id`

## Error Handling

### Duplicate Payment Method Name
```http
POST /api/v1/modalitati-plata/
Status: 409 Conflict
{
  "detail": "A payment method with the name 'revolut_payment' already exists"
}
```

### Missing Required Data
```http
POST /api/v1/modalitati-plata/
Status: 400 Bad Request
{
  "detail": "required_data must contain 'phone_number' for Revolut payment type"
}
```

### Invalid Payment Type
```http
POST /api/v1/modalitati-plata/
Status: 400 Bad Request
{
  "detail": "Payment type with ID 999 does not exist"
}
```

## Best Practices

1. **Display Business Payment Info**: Use `required_fields_schema` and `required_data` to show customers where to send payments
2. **Use Friendly Names**: Display `friendly_name` from payment types to users, not the technical `name`
3. **Validate on Admin Side**: Ensure admins provide required data when creating payment methods
4. **No Customer Input**: Don't ask customers for payment details - they're already stored in the payment method
5. **Icons/Visuals**: Use `payment_type_id` to display appropriate icons (💰 for cash, 💳 for card, 📱 for Revolut, 🏦 for bank transfer)

## Example: Complete Checkout Flow

```javascript
// 1. Fetch payment methods
const paymentMethods = await fetch('/api/v1/modalitati-plata/').then(r => r.json());

// 2. Display payment options to customer
paymentMethods.forEach(method => {
  if (method.payment_type_id === 4) { // Revolut
    console.log(`📱 ${method.description}`);
    console.log(`   Trimiteți la: ${method.required_data.phone_number}`);
  } else if (method.payment_type_id === 5) { // Bank Transfer
    console.log(`🏦 ${method.description}`);
    console.log(`   IBAN: ${method.required_data.iban}`);
    console.log(`   Destinatar: ${method.required_data.recipient_name}`);
  } else {
    console.log(`💳 ${method.description}`);
  }
});

// 3. Customer selects payment method (just the ID)
const order = {
  nume_client: "John Doe",
  payment_method_id: selectedPaymentMethodId, // Just the ID!
  // ... other order fields
};

// 4. Submit order (no payment details needed)
await fetch('/api/v1/orders/', {
  method: 'POST',
  body: JSON.stringify(order)
});
```

## Summary

- **Payment Types**: Predefined categories (cash, card, revolut, bank_transfer, etc.)
- **Payment Methods**: Now include `payment_type_id` and `required_data` (business payment details)
- **Customer Flow**: Simply select a payment method - no additional input needed
- **Admin Flow**: Select payment type and provide business payment details when creating payment methods
- **Display**: Use `required_fields_schema` and `required_data` to show customers where to send payments

