from flask import jsonify, request
import logging

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    """Register error handlers for the Flask application"""
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors"""
        logger.warning(f"Bad request from {request.remote_addr}: {error.description}")
        return jsonify({
            "error": "Bad Request",
            "message": error.description or "Invalid request parameters",
            "status": "error"
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized errors"""
        logger.warning(f"Unauthorized request from {request.remote_addr}")
        return jsonify({
            "error": "Unauthorized",
            "message": "Authentication required",
            "status": "error"
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden errors"""
        logger.warning(f"Forbidden request from {request.remote_addr}")
        return jsonify({
            "error": "Forbidden",
            "message": "Access denied",
            "status": "error"
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors"""
        logger.info(f"Not found: {request.url} from {request.remote_addr}")
        return jsonify({
            "error": "Not Found",
            "message": "The requested resource was not found",
            "path": request.path,
            "status": "error"
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 Method Not Allowed errors"""
        logger.warning(f"Method not allowed: {request.method} {request.url} from {request.remote_addr}")
        return jsonify({
            "error": "Method Not Allowed",
            "message": f"The {request.method} method is not allowed for this endpoint",
            "allowed_methods": error.valid_methods,
            "status": "error"
        }), 405
    
    @app.errorhandler(409)
    def conflict(error):
        """Handle 409 Conflict errors"""
        logger.warning(f"Conflict: {request.url} from {request.remote_addr}")
        return jsonify({
            "error": "Conflict",
            "message": "The request conflicts with the current state of the resource",
            "status": "error"
        }), 409
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        """Handle 422 Unprocessable Entity errors"""
        logger.warning(f"Unprocessable entity: {request.url} from {request.remote_addr}")
        return jsonify({
            "error": "Unprocessable Entity",
            "message": "The request was well-formed but contains semantic errors",
            "status": "error"
        }), 422
    
    @app.errorhandler(429)
    def too_many_requests(error):
        """Handle 429 Too Many Requests errors"""
        logger.warning(f"Rate limit exceeded: {request.remote_addr}")
        return jsonify({
            "error": "Too Many Requests",
            "message": "Rate limit exceeded. Please try again later.",
            "retry_after": getattr(error, 'retry_after', 60),
            "status": "error"
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server Error"""
        logger.error(f"Internal server error: {str(error)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "status": "error"
        }), 500
    
    @app.errorhandler(502)
    def bad_gateway(error):
        """Handle 502 Bad Gateway errors"""
        logger.error(f"Bad gateway error: {str(error)}")
        return jsonify({
            "error": "Bad Gateway",
            "message": "External service temporarily unavailable",
            "status": "error"
        }), 502
    
    @app.errorhandler(503)
    def service_unavailable(error):
        """Handle 503 Service Unavailable errors"""
        logger.error(f"Service unavailable: {str(error)}")
        return jsonify({
            "error": "Service Unavailable",
            "message": "Service temporarily unavailable",
            "status": "error"
        }), 503
    
    @app.errorhandler(504)
    def gateway_timeout(error):
        """Handle 504 Gateway Timeout errors"""
        logger.error(f"Gateway timeout: {str(error)}")
        return jsonify({
            "error": "Gateway Timeout",
            "message": "Request timeout",
            "status": "error"
        }), 504
    
    # Handle general exceptions
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle unhandled exceptions"""
        logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "status": "error"
        }), 500 