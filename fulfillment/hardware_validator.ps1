# =============================================================================
# Hardware Validation Script
#
# Author: Jules
# Date: 2025-09-03
#
# Description:
# This script inspects the local machine for key hardware specifications,
# including CPU, RAM (per stick), and storage devices (per disk).
# It then formats this information into a structured JSON object and outputs
# it to the console.
#
# This output can be captured by a calling application (like our main Python
# fulfillment app) to verify that the hardware configuration matches the
# customer's order.
#
# Usage:
# powershell.exe -ExecutionPolicy Bypass -File .\fulfillment\hardware_validator.ps1
# =============================================================================

# --- Main Function to Orchestrate Hardware Inspection ---
function Get-SystemHardwareAsJson {
    # Create a custom PowerShell object to hold all the hardware details.
    # This acts as a container that we will later convert to JSON.
    $hardwareInfo = [PSCustomObject]@{
        cpu      = $null
        memory   = $null
        storage  = $null
    }

    # --- 1. Get CPU Information ---
    # We retrieve the processor's name, core count, and thread count.
    $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1 Name, NumberOfCores, NumberOfLogicalProcessors
    $hardwareInfo.cpu = @{
        name        = $cpu.Name.Trim()
        cores       = $cpu.NumberOfCores
        threads     = $cpu.NumberOfLogicalProcessors
    }

    # --- 2. Get Memory (RAM) Information ---
    # We loop through each physical memory stick to get its individual details.
    # This is crucial for validating configurations like 2x16GB vs 1x32GB.
    $memorySticks = Get-CimInstance Win32_PhysicalMemory | ForEach-Object {
        @{
            # Capacity is in bytes, so we convert it to Gigabytes (GB).
            capacityGB   = [math]::Round($_.Capacity / 1GB)
            manufacturer = $_.Manufacturer.Trim()
            partNumber   = $_.PartNumber.Trim()
            deviceLocator= $_.DeviceLocator.Trim() # e.g., "ChannelA-DIMM0"
        }
    }
    $hardwareInfo.memory = @{
        totalSticks = $memorySticks.Count
        sticks      = $memorySticks
    }

    # --- 3. Get Storage Device Information ---
    # We loop through each physical disk (not partitions) to get its model and size.
    # This helps differentiate between, for example, a Samsung 1TB SSD and a Crucial 1TB SSD.
    $storageDevices = Get-CimInstance Win32_DiskDrive | Where-Object { $_.MediaType -ne 'Removable Media' } | ForEach-Object {
        @{
            # Size is in bytes, so we convert it to Gigabytes (GB).
            sizeGB      = [math]::Round($_.Size / 1GB)
            model       = $_.Model.Trim()
            serialNumber= $_.SerialNumber.Trim()
            interfaceType= $_.InterfaceType.Trim()
        }
    }
    $hardwareInfo.storage = $storageDevices

    # --- 4. Convert the Final Object to JSON ---
    # We convert the entire PowerShell object into a compact JSON string.
    # This is the final output of the script.
    return $hardwareInfo | ConvertTo-Json -Compress
}

# --- Script Entry Point ---
# Call the main function and write its output to the console.
try {
    Get-SystemHardwareAsJson
}
catch {
    # If any errors occur, output an error JSON object.
    $errorOutput = @{
        error = "An error occurred while inspecting hardware."
        message = $_.Exception.Message
    }
    $errorOutput | ConvertTo-Json -Compress
}
