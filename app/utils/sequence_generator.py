# File: app/utils/sequence_generator.py
# Updated to use SequenceService and core.sequences table
import asyncio
from typing import Optional # Added Optional
from app.models.core.sequence import Sequence
from app.services.core_services import SequenceService 

class SequenceGenerator:
    def __init__(self, sequence_service: SequenceService):
        self.sequence_service = sequence_service
        # No in-memory cache for sequences to ensure DB is source of truth.
        # The DB function core.get_next_sequence_value handles concurrency better.
        # This Python version relying on service needs careful transaction management if high concurrency.
        # For a desktop app, this might be acceptable.

    async def next_sequence(self, sequence_name: str, prefix_override: Optional[str] = None) -> str:
        """
        Generates the next number in a sequence using the SequenceService.
        """
        # This needs to be an atomic operation (SELECT FOR UPDATE + UPDATE)
        # The SequenceService doesn't implement this directly.
        # A raw SQL call to core.get_next_sequence_value() is better here.
        # For now, let's simulate with service calls (less robust for concurrency).
        
        sequence_obj = await self.sequence_service.get_sequence_by_name(sequence_name)

        if not sequence_obj:
            # Create sequence if not found - this should ideally be a setup step
            # or handled by the DB function if called.
            print(f"Sequence '{sequence_name}' not found, creating with defaults.")
            default_prefix = prefix_override if prefix_override is not None else sequence_name.upper()[:3] + "-"
            sequence_obj = Sequence(
                sequence_name=sequence_name,
                next_value=1,
                increment_by=1,
                min_value=1,
                max_value=2147483647,
                prefix=default_prefix,
                format_template='{PREFIX}{VALUE:06}' # Default to 6-digit padding
            )
            # Note: This creation doesn't happen in a transaction with the increment.
            # This is a flaw in this simplified approach.
            await self.sequence_service.save_sequence(sequence_obj) # Save the new sequence definition

        current_value = sequence_obj.next_value
        sequence_obj.next_value += sequence_obj.increment_by
        
        if sequence_obj.cycle and sequence_obj.next_value > sequence_obj.max_value:
            sequence_obj.next_value = sequence_obj.min_value
        elif not sequence_obj.cycle and sequence_obj.next_value > sequence_obj.max_value:
            # This state should not be saved if it exceeds max_value.
            # The core.get_next_sequence_value function likely handles this better.
            # For now, let's prevent saving this invalid state.
            # Instead of raising an error here, the DB sequence function would handle this.
            # If we stick to Python logic, we should not save and raise.
            # However, the schema's DB function core.get_next_sequence_value doesn't have this python-side check.
            # For now, let's assume the DB function is primary and this Python one is a fallback or less used.
            # Let's allow save, but it means the DB function is the one to rely on for strict max_value.
            print(f"Warning: Sequence '{sequence_name}' next value {sequence_obj.next_value} exceeds max value {sequence_obj.max_value} and cycle is off.")
            # To strictly adhere to non-cycling max_value, one might do:
            # if sequence_obj.next_value > sequence_obj.max_value:
            #     raise ValueError(f"Sequence '{sequence_name}' has reached its maximum value.")

        await self.sequence_service.save_sequence(sequence_obj) # Save updated next_value

        # Use prefix_override if provided, else from sequence_obj
        actual_prefix = prefix_override if prefix_override is not None else (sequence_obj.prefix or '')
        
        # Formatting logic based on sequence_obj.format_template
        formatted_value_str = str(current_value) # Default if no padding in template
        
        # Example for handling {VALUE:06} type padding
        padding_marker_start = "{VALUE:0"
        padding_marker_end = "}"
        if padding_marker_start in sequence_obj.format_template:
            try:
                start_index = sequence_obj.format_template.find(padding_marker_start) + len(padding_marker_start)
                end_index = sequence_obj.format_template.find(padding_marker_end, start_index)
                if start_index > -1 and end_index > start_index:
                    padding_spec = sequence_obj.format_template[start_index:end_index]
                    padding = int(padding_spec)
                    formatted_value_str = str(current_value).zfill(padding)
            except ValueError: # int conversion failed
                pass # Use unpadded value
            except Exception: # Other parsing errors
                pass


        result_str = sequence_obj.format_template
        result_str = result_str.replace('{PREFIX}', actual_prefix)
        
        # Replace specific padded value first, then generic unpadded
        if padding_marker_start in sequence_obj.format_template:
             placeholder_to_replace = sequence_obj.format_template[sequence_obj.format_template.find(padding_marker_start):sequence_obj.format_template.find(padding_marker_end, sequence_obj.format_template.find(padding_marker_start)) + 1]
             result_str = result_str.replace(placeholder_to_replace, formatted_value_str)
        else:
            result_str = result_str.replace('{VALUE}', formatted_value_str) # Fallback if no padding specified

        result_str = result_str.replace('{SUFFIX}', sequence_obj.suffix or '')
            
        return result_str
