// Prevent the dashboard from being framed by other sites (clickjacking)
module.exports = function frameProtectionMiddleware(req, res, next) {
  res.setHeader('X-Frame-Options', 'DENY')
  res.setHeader('Content-Security-Policy', "frame-ancestors 'none'")
  next()
}
