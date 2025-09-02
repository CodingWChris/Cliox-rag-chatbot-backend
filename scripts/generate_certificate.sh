#!/bin/bash
# Script to generate self-signed certificate for IAM Roles Anywhere
# This creates the certificate and private key needed for authentication

echo "🔐 Generating self-signed certificate for IAM Roles Anywhere..."

# Create certs directory
mkdir -p certs
cd certs

# Generate private key
echo "📝 Generating private key..."
openssl genrsa -out cliox-chatbot-private-key.pem 2048

# Generate certificate signing request
echo "📝 Generating certificate signing request..."
openssl req -new -key cliox-chatbot-private-key.pem -out cliox-chatbot.csr -subj "/C=US/ST=CA/L=SanFrancisco/O=Cliox/OU=Chatbot/CN=cliox-chatbot"

# Generate self-signed certificate (valid for 1 year)
echo "📝 Generating self-signed certificate..."
openssl x509 -req -in cliox-chatbot.csr -signkey cliox-chatbot-private-key.pem -out cliox-chatbot-certificate.pem -days 365

# Generate certificate bundle (required for AWS)
echo "📝 Creating certificate bundle..."
cp cliox-chatbot-certificate.pem cliox-chatbot-bundle.pem

# Set proper permissions
chmod 600 cliox-chatbot-private-key.pem
chmod 644 cliox-chatbot-certificate.pem cliox-chatbot-bundle.pem

echo "✅ Certificate generation complete!"
echo ""
echo "Generated files:"
echo "  🔑 cliox-chatbot-private-key.pem (keep this secret!)"
echo "  📜 cliox-chatbot-certificate.pem (public certificate)"
echo "  📦 cliox-chatbot-bundle.pem (certificate bundle for AWS)"
echo ""
echo "Next: Register the certificate bundle with AWS IAM Roles Anywhere"
