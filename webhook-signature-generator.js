#!/usr/bin/env node

/**
 * Lashma Webhook HMAC Signature Generator
 * 
 * This script generates HMAC-SHA256 signatures for webhook requests
 * 
 * Usage:
 *   node webhook-signature-generator.js <method> <uri> <body> <secret>
 *   
 * Examples:
 *   node webhook-signature-generator.js \
 *     POST \
 *     "/api/webhooks/insurance-events" \
 *     '{"event_type":"enrollment_created",...}' \
 *     "your_webhook_secret_key_here"
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

// Color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  blue: '\x1b[34m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  cyan: '\x1b[36m',
};

function generateSignature(method, uri, body, secret) {
  const payload = method + uri + body;
  const signature = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');
  return signature;
}

function validateInputs(method, uri, body, secret) {
  const errors = [];
  
  if (!method) errors.push('HTTP method is required');
  if (!uri) errors.push('URI path is required');
  if (body === undefined) errors.push('Request body is required');
  if (!secret) errors.push('Webhook secret is required');
  
  if (method && !['GET', 'POST', 'PUT', 'PATCH', 'DELETE'].includes(method.toUpperCase())) {
    errors.push(`Invalid HTTP method: ${method}`);
  }
  
  if (secret && secret.length < 32) {
    errors.push('⚠️  Warning: Secret should be at least 64 hex characters (256 bits)');
  }
  
  return errors;
}

function printUsage() {
  console.log(`
${colors.cyan}Lashma Webhook HMAC Signature Generator${colors.reset}

${colors.blue}Usage:${colors.reset}
  node webhook-signature-generator.js [options]

${colors.blue}Options:${colors.reset}
  --method <HTTP_METHOD>     HTTP method (POST, GET, etc.)
  --uri <URI_PATH>           URI path (e.g., /api/webhooks/insurance-events)
  --body <JSON_BODY>         Request body as JSON string
  --secret <SECRET_KEY>      Webhook secret key
  --help, -h                 Show this help message
  --interactive, -i          Interactive mode

${colors.blue}Examples:${colors.reset}

  # Generate signature for enrollment event:
  node webhook-signature-generator.js \\
    --method POST \\
    --uri "/api/webhooks/insurance-events" \\
    --body '{"event_type":"enrollment_created","event_id":"evt_123",...}' \\
    --secret "your_secret_key_here"

  # Interactive mode:
  node webhook-signature-generator.js --interactive

${colors.blue}Environment Variables:${colors.reset}
  WEBHOOK_SECRET            Sets default secret (can be overridden with --secret)

${colors.blue}Output:${colors.reset}
  - Signature (hex string)
  - Payload structure
  - Authorization header value
  - cURL command example
  `);
}

function interactiveMode() {
  const readline = require('readline');
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  const questions = [
    { key: 'method', prompt: 'HTTP Method (POST): ' },
    { key: 'uri', prompt: 'URI Path (/api/webhooks/insurance-events): ' },
    { key: 'bodyFile', prompt: 'Path to JSON body file or inline JSON: ' },
    { key: 'secret', prompt: 'Webhook Secret: ' },
  ];

  let answers = { method: 'POST', uri: '/api/webhooks/insurance-events' };
  let questionIndex = 0;

  const askQuestion = () => {
    if (questionIndex >= questions.length) {
      rl.close();
      processInteractiveAnswers(answers);
      return;
    }

    const question = questions[questionIndex];
    const defaultValue = answers[question.key] || '';

    rl.question(
      `${colors.cyan}${question.prompt}${colors.reset}`,
      (answer) => {
        answers[question.key] = answer || defaultValue;
        questionIndex++;
        askQuestion();
      }
    );
  };

  askQuestion();
}

function processInteractiveAnswers(answers) {
  try {
    let body = answers.bodyFile;

    // Check if it's a file
    if (fs.existsSync(answers.bodyFile)) {
      body = fs.readFileSync(answers.bodyFile, 'utf-8');
      console.log(`${colors.green}✓ Loaded body from file${colors.reset}`);
    } else {
      // Try to parse as JSON string
      try {
        JSON.parse(body);
      } catch (e) {
        console.log(`${colors.red}✗ Invalid JSON: ${e.message}${colors.reset}`);
        process.exit(1);
      }
    }

    generateAndDisplay(answers.method, answers.uri, body, answers.secret);
  } catch (error) {
    console.error(`${colors.red}✗ Error:${colors.reset} ${error.message}`);
    process.exit(1);
  }
}

function generateAndDisplay(method, uri, body, secret) {
  const validationErrors = validateInputs(method, uri, body, secret);

  if (validationErrors.length > 0) {
    console.log(`${colors.red}✗ Validation Errors:${colors.reset}`);
    validationErrors.forEach((error) => {
      console.log(`  - ${error}`);
    });
    console.log('');
  }

  const signature = generateSignature(method, uri, body, secret);
  const payload = method + uri + body;

  console.log(`
${colors.green}═════════════════════════════════════════════════════════════${colors.reset}
${colors.green}WEBHOOK SIGNATURE GENERATED${colors.reset}
${colors.green}═════════════════════════════════════════════════════════════${colors.reset}

${colors.blue}Signature (HMAC-SHA256):${colors.reset}
${colors.cyan}${signature}${colors.reset}

${colors.blue}Request Details:${colors.reset}
  Method:        ${colors.cyan}${method}${colors.reset}
  URI:           ${colors.cyan}${uri}${colors.reset}
  Body Length:   ${colors.cyan}${body.length} bytes${colors.reset}
  Payload Size:  ${colors.cyan}${payload.length} bytes${colors.reset}
  Secret Length: ${colors.cyan}${secret.length} chars${colors.reset}

${colors.blue}Authorization Header:${colors.reset}
${colors.cyan}Authorization: Bearer ${signature}${colors.reset}

${colors.blue}cURL Command Example:${colors.reset}
${colors.cyan}curl -X ${method} \\${colors.reset}
${colors.cyan}  -H "Content-Type: application/json" \\${colors.reset}
${colors.cyan}  -H "Authorization: Bearer ${signature}" \\${colors.reset}
${colors.cyan}  -d '${body}' \\${colors.reset}
${colors.cyan}  https://field-tracker.lashma.com/api/webhooks/insurance-events${colors.reset}

${colors.blue}Postman Settings:${colors.reset}
  Add to Authorization header:
  ${colors.cyan}Bearer {{payment_signature}}${colors.reset}

  In Pre-request Script, calculate:
  ${colors.cyan}const sig = generateSignature('POST', '/api/webhooks/insurance-events', body, secret);${colors.reset}
  ${colors.cyan}pm.environment.set('payment_signature', sig);${colors.reset}

${colors.green}═════════════════════════════════════════════════════════════${colors.reset}
  `);
}

// Main execution
const args = process.argv.slice(2);

if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
  printUsage();
  process.exit(0);
}

if (args.includes('--interactive') || args.includes('-i')) {
  interactiveMode();
} else {
  // Parse command-line arguments
  let method = 'POST';
  let uri = '/api/webhooks/insurance-events';
  let body = '';
  let secret = process.env.WEBHOOK_SECRET || '';

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--method':
        method = args[++i];
        break;
      case '--uri':
        uri = args[++i];
        break;
      case '--body':
        body = args[++i];
        break;
      case '--secret':
        secret = args[++i];
        break;
    }
  }

  // Validate we have all required inputs
  const validationErrors = validateInputs(method, uri, body, secret);
  const hasErrors = validationErrors.some(e => !e.includes('⚠️'));

  if (hasErrors) {
    console.log(`${colors.red}✗ Missing required arguments${colors.reset}\n`);
    printUsage();
    process.exit(1);
  }

  generateAndDisplay(method, uri, body, secret);
}
