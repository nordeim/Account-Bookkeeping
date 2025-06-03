# File: tests/unit/utils/test_sequence_generator.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal # Not directly used, but good to have context from other tests

from app.utils.sequence_generator import SequenceGenerator
from app.services.core_services import SequenceService # For mocking interface
from app.models.core.sequence import Sequence as SequenceModel # ORM Model
from app.core.database_manager import DatabaseManager # For mocking db_manager
from app.core.application_core import ApplicationCore # For mocking app_core

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_sequence_service() -> AsyncMock:
    """Fixture to create a mock SequenceService."""
    service = AsyncMock(spec=SequenceService)
    service.get_sequence_by_name = AsyncMock()
    service.save_sequence = AsyncMock(return_value=None) # save_sequence returns the saved object, but mock can be simpler
    return service

@pytest.fixture
def mock_db_manager() -> AsyncMock:
    """Fixture to create a mock DatabaseManager."""
    db_manager = AsyncMock(spec=DatabaseManager)
    db_manager.execute_scalar = AsyncMock()
    # Mock logger on db_manager if SequenceGenerator tries to use it
    db_manager.logger = AsyncMock(spec=logging.Logger)
    db_manager.logger.warning = MagicMock()
    db_manager.logger.error = MagicMock()
    db_manager.logger.info = MagicMock()
    return db_manager

@pytest.fixture
def mock_app_core(mock_db_manager: AsyncMock, mock_sequence_service: AsyncMock) -> MagicMock:
    """Fixture to create a mock ApplicationCore providing mocked db_manager and sequence_service."""
    app_core = MagicMock(spec=ApplicationCore)
    app_core.db_manager = mock_db_manager
    app_core.sequence_service = mock_sequence_service # Though SequenceGenerator takes service directly
    app_core.logger = MagicMock(spec=logging.Logger) # Mock logger on app_core too
    return app_core

@pytest.fixture
def sequence_generator(mock_sequence_service: AsyncMock, mock_app_core: MagicMock) -> SequenceGenerator:
    """Fixture to create a SequenceGenerator instance."""
    # SequenceGenerator constructor: sequence_service, app_core_ref
    return SequenceGenerator(sequence_service=mock_sequence_service, app_core_ref=mock_app_core)

# --- Test Cases ---

async def test_next_sequence_db_function_success(
    sequence_generator: SequenceGenerator, 
    mock_app_core: MagicMock
):
    """Test successful sequence generation using the database function."""
    sequence_name = "SALES_INVOICE"
    expected_formatted_value = "INV-000123"
    mock_app_core.db_manager.execute_scalar.return_value = expected_formatted_value

    result = await sequence_generator.next_sequence(sequence_name)
    
    assert result == expected_formatted_value
    mock_app_core.db_manager.execute_scalar.assert_awaited_once_with(
        f"SELECT core.get_next_sequence_value('{sequence_name}');"
    )

async def test_next_sequence_db_function_returns_none_fallback(
    sequence_generator: SequenceGenerator,
    mock_app_core: MagicMock,
    mock_sequence_service: AsyncMock
):
    """Test Python fallback when DB function returns None."""
    sequence_name = "PURCHASE_ORDER"
    mock_app_core.db_manager.execute_scalar.return_value = None # Simulate DB function failure

    # Setup for Python fallback
    mock_sequence_orm = SequenceModel(
        id=1, sequence_name=sequence_name, prefix="PO", next_value=10, 
        increment_by=1, min_value=1, max_value=9999, cycle=False,
        format_template="{PREFIX}-{VALUE:04d}" # Ensure 'd' for integer formatting
    )
    mock_sequence_service.get_sequence_by_name.return_value = mock_sequence_orm
    mock_sequence_service.save_sequence.side_effect = lambda seq_obj: seq_obj # Return the object passed to it

    result = await sequence_generator.next_sequence(sequence_name)

    assert result == "PO-0010"
    mock_app_core.db_manager.execute_scalar.assert_awaited_once()
    mock_sequence_service.get_sequence_by_name.assert_awaited_once_with(sequence_name)
    mock_sequence_service.save_sequence.assert_awaited_once()
    assert mock_sequence_orm.next_value == 11 # Check increment

async def test_next_sequence_db_function_exception_fallback(
    sequence_generator: SequenceGenerator,
    mock_app_core: MagicMock,
    mock_sequence_service: AsyncMock
):
    """Test Python fallback when DB function raises an exception."""
    sequence_name = "JOURNAL_ENTRY"
    mock_app_core.db_manager.execute_scalar.side_effect = Exception("DB connection error")

    mock_sequence_orm = SequenceModel(
        id=2, sequence_name=sequence_name, prefix="JE", next_value=1, 
        increment_by=1, format_template="{PREFIX}{VALUE:06d}"
    )
    mock_sequence_service.get_sequence_by_name.return_value = mock_sequence_orm
    mock_sequence_service.save_sequence.side_effect = lambda seq_obj: seq_obj

    result = await sequence_generator.next_sequence(sequence_name)

    assert result == "JE000001"
    mock_app_core.db_manager.execute_scalar.assert_awaited_once()
    mock_sequence_service.get_sequence_by_name.assert_awaited_once_with(sequence_name)

async def test_next_sequence_python_fallback_new_sequence(
    sequence_generator: SequenceGenerator,
    mock_app_core: MagicMock, # For db_manager to be present on app_core
    mock_sequence_service: AsyncMock
):
    """Test Python fallback creates a new sequence if not found in DB."""
    sequence_name = "NEW_SEQ"
    # Simulate DB function failure (e.g., returns None or raises error, leading to fallback)
    mock_app_core.db_manager.execute_scalar.return_value = None 
    mock_sequence_service.get_sequence_by_name.return_value = None # Sequence not found

    # The save_sequence mock should capture the argument passed to it
    # so we can assert its properties.
    saved_sequence_holder = {}
    async def capture_save(seq_obj):
        saved_sequence_holder['seq'] = seq_obj
        return seq_obj
    mock_sequence_service.save_sequence.side_effect = capture_save
    
    result = await sequence_generator.next_sequence(sequence_name)

    assert result == "NEW-000001" # Based on default prefix logic and format_template
    
    # Check that get_sequence_by_name was called
    mock_sequence_service.get_sequence_by_name.assert_awaited_once_with(sequence_name)
    
    # Check that save_sequence was called (once for creation, once for update)
    assert mock_sequence_service.save_sequence.await_count == 2
    
    # Check the details of the created sequence object
    created_seq = saved_sequence_holder['seq']
    assert created_seq.sequence_name == sequence_name
    assert created_seq.prefix == "NEW" # Default prefix logic: sequence_name.upper()[:3]
    assert created_seq.next_value == 2 # Initial value was 1, used, then incremented
    assert created_seq.format_template == "{PREFIX}-{VALUE:06d}"


async def test_next_sequence_python_fallback_prefix_override(
    sequence_generator: SequenceGenerator,
    mock_app_core: MagicMock,
    mock_sequence_service: AsyncMock
):
    """Test Python fallback with prefix_override."""
    sequence_name = "ITEM_CODE"
    # DB function is skipped when prefix_override is used, so mock it to ensure it's not called.
    mock_app_core.db_manager.execute_scalar.side_effect = AssertionError("DB function should not be called with prefix_override")

    mock_sequence_orm = SequenceModel(
        id=3, sequence_name=sequence_name, prefix="ITM", next_value=5, 
        increment_by=1, format_template="{PREFIX}-{VALUE:03d}"
    )
    mock_sequence_service.get_sequence_by_name.return_value = mock_sequence_orm
    mock_sequence_service.save_sequence.side_effect = lambda seq_obj: seq_obj
    
    result = await sequence_generator.next_sequence(sequence_name, prefix_override="OVERRIDE")

    assert result == "OVERRIDE-005"
    mock_app_core.db_manager.execute_scalar.assert_not_awaited() # Verify DB func not called
    mock_sequence_service.get_sequence_by_name.assert_awaited_once_with(sequence_name)
    assert mock_sequence_orm.next_value == 6

async def test_next_sequence_python_fallback_cycle(
    sequence_generator: SequenceGenerator,
    mock_app_core: MagicMock,
    mock_sequence_service: AsyncMock
):
    """Test Python fallback sequence cycling."""
    sequence_name = "CYCLE_SEQ"
    mock_app_core.db_manager.execute_scalar.return_value = None # Force Python fallback

    mock_sequence_orm = SequenceModel(
        id=4, sequence_name=sequence_name, prefix="CY", next_value=3, 
        increment_by=1, min_value=1, max_value=3, cycle=True,
        format_template="{PREFIX}{VALUE}"
    )
    mock_sequence_service.get_sequence_by_name.return_value = mock_sequence_orm
    mock_sequence_service.save_sequence.side_effect = lambda seq_obj: seq_obj

    result1 = await sequence_generator.next_sequence(sequence_name) # Uses 3, next_value becomes 1 (cycles)
    assert result1 == "CY3"
    assert mock_sequence_orm.next_value == 1 # Cycled

    result2 = await sequence_generator.next_sequence(sequence_name) # Uses 1, next_value becomes 2
    assert result2 == "CY1"
    assert mock_sequence_orm.next_value == 2

async def test_next_sequence_python_fallback_max_value_no_cycle(
    sequence_generator: SequenceGenerator,
    mock_app_core: MagicMock,
    mock_sequence_service: AsyncMock
):
    """Test Python fallback hitting max value without cycling."""
    sequence_name = "MAX_SEQ"
    mock_app_core.db_manager.execute_scalar.return_value = None

    mock_sequence_orm = SequenceModel(
        id=5, sequence_name=sequence_name, prefix="MX", next_value=3, 
        increment_by=1, min_value=1, max_value=3, cycle=False, # cycle=False
        format_template="{PREFIX}{VALUE}"
    )
    mock_sequence_service.get_sequence_by_name.return_value = mock_sequence_orm
    mock_sequence_service.save_sequence.side_effect = lambda seq_obj: seq_obj

    result = await sequence_generator.next_sequence(sequence_name) # Uses 3, next_value becomes 4
    assert result == "MX3"
    assert mock_sequence_orm.next_value == 4 

    # Next call should raise ValueError
    with pytest.raises(ValueError) as excinfo:
        await sequence_generator.next_sequence(sequence_name)
    assert f"Sequence '{sequence_name}' has reached its maximum value (3) and cannot cycle." in str(excinfo.value)

async def test_next_sequence_format_template_zfill_variant(
    sequence_generator: SequenceGenerator,
    mock_app_core: MagicMock,
    mock_sequence_service: AsyncMock
):
    """Test a format_template with {VALUE:06} (no 'd')."""
    sequence_name = "ZFILL_TEST"
    mock_app_core.db_manager.execute_scalar.return_value = None

    mock_sequence_orm = SequenceModel(
        id=6, sequence_name=sequence_name, prefix="ZF", next_value=7,
        increment_by=1, format_template="{PREFIX}{VALUE:06}" # Note: no 'd'
    )
    mock_sequence_service.get_sequence_by_name.return_value = mock_sequence_orm
    mock_sequence_service.save_sequence.side_effect = lambda seq_obj: seq_obj

    result = await sequence_generator.next_sequence(sequence_name)
    assert result == "ZF000007"
