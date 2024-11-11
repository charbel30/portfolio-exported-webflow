// Enhanced Webflow Usage Analyzer
console.log('=== Enhanced Webflow Analyzer Starting ===');

// Store original Webflow object structure
const originalWebflow = window.Webflow || {};
console.log('Original Webflow object keys:', Object.keys(originalWebflow));
console.log('Original Webflow object methods:', 
    Object.getOwnPropertyNames(originalWebflow).filter(prop => 
        typeof originalWebflow[prop] === 'function'
    )
);

// Enhanced usage data structure
const usageData = {
    functionCalls: {},
    propertyAccess: new Set(),
    events: new Set(),
    startTime: Date.now(),
    pageLoadTime: null
};

// Helper to get stack trace
function getStackTrace() {
    try {
        throw new Error();
    } catch (error) {
        return error.stack
            .split('\n')
            .slice(2) // Remove error message and this function
            .map(line => line.trim())
            .filter(line => !line.includes('analyze-webflow.js')); // Filter out our analyzer
    }
}

// Create enhanced proxy
window.Webflow = new Proxy(originalWebflow, {
    get(target, prop) {
        const timestamp = Date.now();
        const relativeTime = timestamp - usageData.startTime;
        
        // Log property access with timing
        console.log(`[${relativeTime}ms] Accessing Webflow.${prop}`);
        usageData.propertyAccess.add(prop);

        const value = target[prop];
        
        // If it's a function, wrap it to track detailed usage
        if (typeof value === 'function') {
            return function(...args) {
                const callTimestamp = Date.now();
                const callRelativeTime = callTimestamp - usageData.startTime;
                const stack = getStackTrace();
                
                console.log(`[${callRelativeTime}ms] Calling Webflow.${prop}()`, 
                    '\nArguments:', args.map(arg => typeof arg),
                    '\nStack:', stack[0]
                );
                
                // Track detailed function call
                if (!usageData.functionCalls[prop]) {
                    usageData.functionCalls[prop] = [];
                }
                usageData.functionCalls[prop].push({
                    timestamp: callTimestamp,
                    relativeTime: callRelativeTime,
                    argTypes: args.map(arg => typeof arg),
                    stack: stack,
                    pagePhase: document.readyState
                });
                
                return value.apply(this, args);
            };
        }
        
        return value;
    }
});

// Enhanced event listener tracking
const originalAddEventListener = EventTarget.prototype.addEventListener;
EventTarget.prototype.addEventListener = function(type, listener, options) {
    const timestamp = Date.now();
    const relativeTime = timestamp - usageData.startTime;
    const stack = getStackTrace();
    
    console.log(`[${relativeTime}ms] Event listener added: ${type}`, 
        '\nStack:', stack[0]
    );
    
    usageData.events.add({
        type,
        timestamp,
        relativeTime,
        stack: stack[0],
        target: this.tagName || this.toString()
    });
    
    return originalAddEventListener.call(this, type, listener, options);
};

// Enhanced usage report
function printUsageReport() {
    const now = Date.now();
    const totalTime = now - usageData.startTime;
    
    console.log('\n=== Detailed Webflow Usage Report ===\n');
    console.log(`Total time: ${totalTime}ms`);
    console.log(`Page load time: ${usageData.pageLoadTime}ms`);
    
    console.log('\nAccessed Properties:');
    console.log([...usageData.propertyAccess]);
    
    console.log('\nFunction Calls by Timing:');
    Object.entries(usageData.functionCalls).forEach(([func, calls]) => {
        console.log(`\n${func}:`);
        console.log(`  Total calls: ${calls.length}`);
        console.log('  First call:', {
            time: calls[0].relativeTime + 'ms',
            phase: calls[0].pagePhase,
            stack: calls[0].stack[0]
        });
        if (calls.length > 1) {
            console.log('  Last call:', {
                time: calls[calls.length - 1].relativeTime + 'ms',
                phase: calls[calls.length - 1].pagePhase,
                stack: calls[calls.length - 1].stack[0]
            });
        }
    });
    
    console.log('\nEvent Listeners:');
    const eventsByType = {};
    usageData.events.forEach(event => {
        if (!eventsByType[event.type]) {
            eventsByType[event.type] = [];
        }
        eventsByType[event.type].push(event);
    });
    Object.entries(eventsByType).forEach(([type, events]) => {
        console.log(`\n${type}:`);
        console.log(`  Count: ${events.length}`);
        console.log('  Targets:', [...new Set(events.map(e => e.target))]);
    });
    
    // Identify unused functions
    const definedFunctions = Object.getOwnPropertyNames(originalWebflow)
        .filter(prop => typeof originalWebflow[prop] === 'function');
    const usedFunctions = Object.keys(usageData.functionCalls);
    const unusedFunctions = definedFunctions.filter(f => !usedFunctions.includes(f));
    
    console.log('\nPotentially Unused Functions:');
    console.log(unusedFunctions);
    
    // Export data
    const exportData = {
        summary: {
            totalTime,
            pageLoadTime: usageData.pageLoadTime,
            totalFunctionCalls: Object.values(usageData.functionCalls)
                .reduce((sum, calls) => sum + calls.length, 0),
            totalEventListeners: usageData.events.size,
            unusedFunctions
        },
        details: {
            functionCalls: usageData.functionCalls,
            propertyAccess: [...usageData.propertyAccess],
            events: [...usageData.events]
        }
    };
    
    console.log('\nExport data available as window.webflowUsageData');
    window.webflowUsageData = exportData;
}

// Track page load time
window.addEventListener('load', () => {
    usageData.pageLoadTime = Date.now() - usageData.startTime;
    printUsageReport();
});

// Expose utilities
window.printWebflowUsage = printUsageReport;
window.checkWebflowFunction = (functionName) => {
    const calls = usageData.functionCalls[functionName] || [];
    console.log(`\nDetailed usage for ${functionName}:`);
    console.log(`Total calls: ${calls.length}`);
    if (calls.length > 0) {
        calls.forEach((call, i) => {
            console.log(`\nCall ${i + 1}:`);
            console.log('Time:', call.relativeTime + 'ms');
            console.log('Page phase:', call.pagePhase);
            console.log('Stack:', call.stack[0]);
            console.log('Argument types:', call.argTypes);
        });
    }
};

console.log('Enhanced Webflow Analyzer Ready');
