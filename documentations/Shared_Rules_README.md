# Shared Development Rules for Flight Booking Portal

This directory contains the centralized development rules and standards that are used across both the Backend (Python/Quart) and Frontend (Next.js/TypeScript) components of the flight booking system.

## Rules Structure

### `.cursorrules-api`
- RESTful API design principles for flight booking systems
- HTTP method usage and status code standards
- Authentication and authorization patterns for airline APIs
- External system integration patterns (NDC APIs, GDS, payment gateways)
- Performance optimization and monitoring for travel systems

### `.cursorrules-database`
- Redis best practices for flight data caching
- Database query patterns for booking operations
- Data security and compliance for travel systems (PCI, GDPR)
- Backup and recovery strategies for booking data
- Performance monitoring for flight search operations

### `.cursorrules-dev`
- Python development practices for flight booking systems
- Modular design principles and separation of concerns
- NDC API integration standards
- Code quality requirements and testing practices
- Security and performance considerations

### `.cursorrules-documentation`
- Documentation standards for travel technology systems
- Planning document requirements for flight booking features
- Airline integration documentation guidelines
- Markdown standards and quality requirements
- Review and update processes for travel system documentation

### `.cursorrules-methodology`
- Development methodology and constraints for flight booking systems
- Error handling philosophy for travel systems
- Testing requirements and quality assurance standards
- Production deployment and monitoring standards
- Security and compliance requirements

### `.cursorrules-security`
- Travel industry data protection requirements
- Payment Card Industry (PCI) compliance standards
- Aviation security and regulatory compliance
- Passenger privacy protection and audit requirements
- Business continuity and incident response procedures

### `.cursorrules-frontend`
- Next.js 14+ with App Router architecture standards
- TypeScript and React component patterns for flight booking
- Tailwind CSS + shadcn/ui styling and accessibility requirements
- Clerk authentication and user management integration
- Prisma database integration and API communication patterns

## Usage

These rules are automatically included in both Backend and Frontend projects through their respective `.cursorrules` files:

- **Backend**: `Backend/.cursorrules` includes all shared rules + backend-specific rules
- **Frontend**: `Frontend/.cursorrules` includes all shared rules + frontend-specific rules

## Benefits of Centralized Rules

1. **Consistency**: Ensures consistent development practices across both frontend and backend
2. **Maintainability**: Single source of truth for updating development standards
3. **Compliance**: Centralized security and compliance requirements for aviation industry
4. **Efficiency**: Reduces duplication and ensures all team members follow the same standards
5. **Scalability**: Easy to extend rules for new services or components

## Updating Shared Rules

When updating shared rules:

1. Make changes in the appropriate `.cursorrules-*` file in this directory
2. Test changes don't break existing functionality in both Backend and Frontend
3. Document any breaking changes or new requirements
4. Ensure compliance with aviation industry standards and regulations
5. Update this README if rule structure changes

## Aviation Industry Standards Covered

- **NDC (New Distribution Capability)**: Modern airline API integration standards
- **PCI DSS**: Payment card industry security standards for booking systems
- **GDPR**: European data protection regulations for passenger information
- **IATA Standards**: International Air Transport Association guidelines
- **TSA/Aviation Security**: Transportation security and passenger screening requirements

## Integration with Development Tools

These rules are designed to work with:
- Cursor IDE for intelligent code completion and suggestions
- Airline sandbox APIs for testing flight booking integrations  
- Payment processor sandbox environments for secure payment testing
- Aviation industry certification and compliance validation tools