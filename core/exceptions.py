"""Exception hierarchy. Recoverable errors are retried; permanent errors are not."""

class WorkflowError(Exception): pass

class RecoverableError(WorkflowError): pass
class ToolFailure(RecoverableError): pass
class AgentTimeout(RecoverableError): pass

class PermanentError(WorkflowError): pass
class InvalidInputError(PermanentError): pass
class MissingDataError(PermanentError): pass
class InvalidOutputError(PermanentError): pass

class SecurityViolation(PermanentError): pass
class UnauthorizedToolAccess(SecurityViolation): pass
class UnauthorizedStateWrite(SecurityViolation): pass

class WorkflowAborted(WorkflowError): pass
