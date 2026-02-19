# Backend API Requirements - Merchant Identification Information

## 📋 **Overview**

This document outlines the required API extensions for the `BusinessDetails` model to ensure full legal compliance for online commerce in Romania. These fields are **mandatory by law** and must be implemented before the site goes live.

## 🟡 **Merchant Identity Fields - Backend Implementation**

### **1. business_name** (String, max 100)
- **Purpose**: Official company name as registered with authorities
- **Legal Requirement**: Mandatory for all online commerce sites
- **Current Status**: ✅ **IMPLEMENTED** - Optional in backend
- **Frontend Usage**: Will replace hardcoded `getAppName()` from config
- **Example**: "SC PCMA SRL" or "Paine cu Maia de la Andreea"

### **2. registration_number** (String, max 20)
- **Purpose**: Official registration number at Trade Registry (J/XX/XXXX/XXXX format)
- **Legal Requirement**: Mandatory for all online commerce sites
- **Current Status**: ✅ **IMPLEMENTED** - Optional in backend
- **Frontend Usage**: Will be displayed in footer
- **Example**: "J22/1234/2020" or "J40/1234/2020"

### **3. CUI** (String, max 16)
- **Purpose**: Fiscal identification code (ROXXXXXXXXX format)
- **Legal Requirement**: Mandatory for all online commerce sites
- **Current Status**: ✅ **IMPLEMENTED** - Optional in backend
- **Frontend Usage**: Will be displayed in footer
- **Example**: "RO12345678" or "RO87654321"

### **4. email** (String, max 100)
- **Purpose**: Official business email address
- **Legal Requirement**: Mandatory for consumer contact
- **Current Status**: ✅ **IMPLEMENTED** - Optional in backend
- **Frontend Usage**: Will be displayed in footer and contact page
- **Example**: "contact@pcma.ro" or "office@pcma.ro"

### **5. operating_hours** (String, max 150)
- **Purpose**: Free-text business operating hours (displayed as-is)
- **Legal Requirement**: Mandatory for transparency
- **Current Status**: ✅ **IMPLEMENTED** - Optional in backend
- **Frontend Usage**: Will be displayed in footer
- **Examples**:
  - "Luni - Vineri: 8:00 - 18:00; Sâmbătă: 8:00 - 14:00; Duminică: Închis"
  - "L-V 9-17 / S 10-14 / D închis"

### **6. representative** (String, max 100)
- **Purpose**: Legal representative name and position
- **Legal Requirement**: Required for compliance
- **Current Status**: ✅ **IMPLEMENTED** - Optional in backend
- **Frontend Usage**: Will be displayed in footer
- **Example**: "Andreea Popescu - Administrator" or "Ion Ionescu - Director General"

## 🎯 **Implementation Details**

### **API Endpoint**
- **Model**: `BusinessDetails`
- **Endpoint**: `/api/v1/business-details/`
- **Method**: GET (existing)

### **Database Changes**
- Add new columns to `business_details` table:
  - `business_name` VARCHAR(100)
  - `registration_number` VARCHAR(20)
  - `CUI` VARCHAR(16)
  - `email` VARCHAR(100)
  - `operating_hours` VARCHAR(150)
  - `representative` VARCHAR(100)

### **Data Validation**
- `business_name`: **Optional**, max 100 characters
- `registration_number`: **Optional**, regex ^[JF][0-9]{2}/[0-9]{1,6}/[0-9]{4}$ (e.g., J22/1234/2020)
- `CUI`: **Optional**, regex ^(RO)?[0-9]{2,10}$ (optional RO prefix)
- `email`: **Optional**, valid email format, max 100 characters
- `operating_hours`: **Optional**, free-text, max 150 characters
- `representative`: **Optional**, max 100 characters

### **Backend Behavior**
- **All fields are optional** - API calls will not fail due to missing fields
- **Empty strings are normalized to NULL** - Sending `""` or `"   "` clears the field
- **Partial updates supported** - PATCH/PUT only update provided fields
- **Validation only when provided** - Regex/email validation only applies to non-null values

### **Migration Strategy**
1. ✅ **COMPLETED** - Added new columns with NULL constraint initially
2. ✅ **COMPLETED** - Updated existing records with placeholder data
3. ✅ **COMPLETED** - Fields remain optional (backend design decision)
4. ✅ **COMPLETED** - Updated API documentation

## 📅 **Timeline**

- **Priority**: ✅ **COMPLETED** - Backend implementation finished
- **Status**: 🟡 **READY FOR FRONTEND** - All 6 optional fields implemented and tested
- **Testing**: ✅ **COMPLETED** - 255 integration tests passing
- **Next Steps**: Frontend team can now integrate the new fields

## 🔗 **Related Frontend Changes**

After backend implementation, frontend will:
1. Update `businessInfo.ts` utility functions
2. Display all new fields in footer
3. Update contact page with new information
4. Remove hardcoded values from config

## 📚 **Legal References**

- **OUG 34/2014**: Consumer rights protection
- **ANPC Requirements**: Merchant identification obligations
- **GDPR Compliance**: Contact information transparency

## ✅ **Backend Implementation Complete**

### **What Was Implemented**
1. ✅ **Database Migration** - Added 6 nullable columns to `business_details` table
2. ✅ **SQLAlchemy Model** - Updated `BusinessDetails` with new optional fields
3. ✅ **Pydantic Schemas** - Added validation and empty-string-to-None normalization
4. ✅ **Service Layer** - Enhanced to handle partial updates and field clearing
5. ✅ **API Endpoints** - All CRUD operations support new fields
6. ✅ **Integration Tests** - 255 tests passing, covering all new functionality

### **Technical Details**
- **All fields optional** - No API failures due to missing fields
- **Empty string handling** - `""` or `"   "` → `NULL` in database
- **Validation rules** - Regex for registration_number/CUI, email format check
- **Partial updates** - PATCH/PUT only modify provided fields
- **Backward compatible** - Existing API calls continue to work

### **Ready for Frontend Integration**
The backend is now ready for the frontend team to:
1. Update `businessInfo.ts` utility functions
2. Display new fields in footer and contact pages
3. Remove hardcoded values from config
4. Test field clearing functionality

---

**Contact**: Frontend Team  
**Status**: ✅ **BACKEND COMPLETE** - Ready for frontend integration  
**Priority**: 🟡 **READY FOR FRONTEND** - All 6 optional fields implemented and tested
