# bot/performance_optimizer.py
import asyncio
import logging
import time
import os
from typing import Dict, List, Optional, Any, Callable
from functools import wraps, lru_cache
from concurrent.futures import ThreadPoolExecutor
import threading
import weakref
from collections import defaultdict
import json


class CacheManager:
    """Advanced caching system for improved performance"""
    
    def __init__(self):
        self.logger = logging.getLogger('CacheManager')
        self.cache_stats = defaultdict(int)
        
        # Different cache stores for different types of data
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_cache: Dict[str, float] = {}  # TTL timestamps
        
        # Cache configuration
        self.default_ttl = 300  # 5 minutes
        self.max_cache_size = 10000
        
        # Cleanup task - don't start it automatically to avoid issues during import
        self.cleanup_task: Optional[asyncio.Task] = None
    
    def start_cleanup_task(self):
        """Start background cleanup task - call this after event loop is running"""
        if self.cleanup_task is None or self.cleanup_task.done():
            try:
                # Only start cleanup task if there's a running event loop
                try:
                    loop = asyncio.get_running_loop()
                    if loop.is_running():
                        self.cleanup_task = asyncio.create_task(self._cleanup_expired_cache())
                    else:
                        # Event loop not running, will start cleanup when needed
                        pass
                except RuntimeError:
                    # No event loop running
                    pass
            except Exception:
                # Any other error, just don't start the cleanup task
                pass
    
    async def _cleanup_expired_cache(self):
        """Clean up expired cache entries"""
        while True:
            try:
                current_time = time.time()
                expired_keys = []
                
                for key, expiry_time in self.ttl_cache.items():
                    if current_time > expiry_time:
                        expired_keys.append(key)
                
                for key in expired_keys:
                    self._remove_cache_entry(key)
                
                # Sleep for 1 minute
                await asyncio.sleep(60)
                
            except Exception as e:
                self.logger.error(f"Error in cache cleanup: {e}")
                await asyncio.sleep(60)
    
    def _remove_cache_entry(self, key: str):
        """Remove a cache entry"""
        if key in self.memory_cache:
            del self.memory_cache[key]
        if key in self.ttl_cache:
            del self.ttl_cache[key]
        self.cache_stats['evictions'] += 1
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a cache entry"""
        try:
            # Check cache size limit
            if len(self.memory_cache) >= self.max_cache_size:
                # Remove oldest entries (simple LRU)
                oldest_keys = list(self.memory_cache.keys())[:100]  # Remove 100 oldest
                for old_key in oldest_keys:
                    self._remove_cache_entry(old_key)
            
            # Set cache entry
            self.memory_cache[key] = {
                'value': value,
                'timestamp': time.time()
            }
            
            # Set TTL
            ttl = ttl or self.default_ttl
            self.ttl_cache[key] = time.time() + ttl
            
            self.cache_stats['sets'] += 1
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get a cache entry"""
        try:
            # Check if key exists and is not expired
            current_time = time.time()
            
            if key not in self.memory_cache:
                self.cache_stats['misses'] += 1
                return None
            
            if key in self.ttl_cache and current_time > self.ttl_cache[key]:
                # Expired
                self._remove_cache_entry(key)
                self.cache_stats['misses'] += 1
                return None
            
            self.cache_stats['hits'] += 1
            return self.memory_cache[key]['value']
            
        except Exception as e:
            self.logger.error(f"Error getting cache key {key}: {e}")
            self.cache_stats['errors'] += 1
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a cache entry"""
        try:
            if key in self.memory_cache:
                self._remove_cache_entry(key)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all cache entries"""
        try:
            self.memory_cache.clear()
            self.ttl_cache.clear()
            self.cache_stats['clears'] += 1
            return True
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'evictions': self.cache_stats['evictions'],
            'errors': self.cache_stats['errors'],
            'clears': self.cache_stats['clears'],
            'hit_rate_percent': hit_rate,
            'total_requests': total_requests,
            'current_size': len(self.memory_cache)
        }


class TaskPoolManager:
    """Manages concurrent task execution with resource limits"""
    
    def __init__(self, max_workers: int = 10):
        self.logger = logging.getLogger('TaskPoolManager')
        self.max_workers = max_workers
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.active_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
    
    async def run_in_thread(self, func: Callable, *args, **kwargs) -> Any:
        """Run a synchronous function in a thread pool"""
        loop = asyncio.get_event_loop()
        self.active_tasks += 1
        
        try:
            result = await loop.run_in_executor(
                self.thread_pool, 
                lambda: func(*args, **kwargs)
            )
            self.completed_tasks += 1
            return result
        except Exception as e:
            self.failed_tasks += 1
            raise
        finally:
            self.active_tasks = max(0, self.active_tasks - 1)
    
    async def run_concurrent_tasks(self, tasks: List[Callable]) -> List[Any]:
        """Run multiple tasks concurrently with rate limiting"""
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def run_task_with_semaphore(task):
            async with semaphore:
                return await self.run_in_thread(task)
        
        # Run all tasks concurrently
        results = await asyncio.gather(
            *[run_task_with_semaphore(task) for task in tasks],
            return_exceptions=True
        )
        
        # Update stats
        successful_results = [r for r in results if not isinstance(r, Exception)]
        failed_results = [r for r in results if isinstance(r, Exception)]
        
        self.completed_tasks += len(successful_results)
        self.failed_tasks += len(failed_results)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get task pool statistics"""
        return {
            'max_workers': self.max_workers,
            'active_tasks': self.active_tasks,
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'total_tasks': self.completed_tasks + self.failed_tasks
        }
    
    def shutdown(self, wait: bool = True):
        """Shutdown the thread pool"""
        self.thread_pool.shutdown(wait=wait)


class PerformanceOptimizer:
    """Main performance optimization service"""
    
    def __init__(self):
        self.logger = logging.getLogger('PerformanceOptimizer')
        
        # Initialize performance components
        self.cache_manager = CacheManager()
        self.task_pool = TaskPoolManager()
        
        # Performance monitoring
        self.performance_metrics = defaultdict(list)
        self.optimization_history = []
        
        self.logger.info("Performance optimizer initialized")
    
    def start_background_tasks(self):
        """Start background tasks like cache cleanup"""
        self.cache_manager.start_cleanup_task()
    
    def cached(self, ttl: int = 300, key_prefix: str = ""):
        """Decorator for caching function results"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = f"{key_prefix}{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
                
                # Try to get from cache
                cached_result = self.cache_manager.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function
                start_time = time.time()
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Store in cache
                self.cache_manager.set(cache_key, result, ttl)
                
                # Record performance metrics
                self.record_performance_metric(func.__name__, execution_time, 'cache_miss')
                
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = f"{key_prefix}{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
                
                # Try to get from cache
                cached_result = self.cache_manager.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function
                start_time = time.time()
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Store in cache
                self.cache_manager.set(cache_key, result, ttl)
                
                # Record performance metrics
                self.record_performance_metric(func.__name__, execution_time, 'cache_miss')
                
                return result
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
                
        return decorator
    
    def timed(self, operation_name: Optional[str] = None):
        """Decorator for timing function execution"""
        def decorator(func):
            op_name = operation_name or func.__name__
            
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    self.record_performance_metric(op_name, execution_time, 'success')
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    self.record_performance_metric(op_name, execution_time, 'error')
                    raise
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    self.record_performance_metric(op_name, execution_time, 'success')
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    self.record_performance_metric(op_name, execution_time, 'error')
                    raise
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
                
        return decorator
    
    def record_performance_metric(self, operation: str, execution_time: float, status: str):
        """Record a performance metric"""
        metric = {
            'timestamp': time.time(),
            'operation': operation,
            'execution_time': execution_time,
            'status': status
        }
        
        self.performance_metrics[operation].append(metric)
        
        # Keep only last 1000 metrics per operation
        if len(self.performance_metrics[operation]) > 1000:
            self.performance_metrics[operation] = self.performance_metrics[operation][-1000:]
    
    async def batch_process(self, items: List[Any], processor: Callable, batch_size: int = 100) -> List[Any]:
        """Process items in optimized batches"""
        try:
            results = []
            total_items = len(items)
            
            for i in range(0, total_items, batch_size):
                batch = items[i:i + batch_size]
                
                # Create concurrent tasks for batch
                batch_tasks = [
                    lambda item=item: processor(item) for item in batch
                ]
                
                # Process batch concurrently
                batch_results = await self.task_pool.run_concurrent_tasks(batch_tasks)
                results.extend(batch_results)
                
                # Small delay to prevent overwhelming the system
                if i + batch_size < total_items:
                    await asyncio.sleep(0.01)
            
            self.record_performance_metric('batch_process', len(items), 'success')
            return results
            
        except Exception as e:
            self.logger.error(f"Batch processing error: {e}")
            self.record_performance_metric('batch_process', len(items), 'error')
            raise
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        try:
            report = {
                'timestamp': time.time(),
                'cache_stats': self.cache_manager.get_stats(),
                'task_pool_stats': self.task_pool.get_stats(),
                'operation_metrics': {}
            }
            
            # Analyze operation metrics
            for operation, metrics in self.performance_metrics.items():
                if not metrics:
                    continue
                
                execution_times = [m['execution_time'] for m in metrics]
                success_count = len([m for m in metrics if m['status'] == 'success'])
                error_count = len([m for m in metrics if m['status'] == 'error'])
                
                report['operation_metrics'][operation] = {
                    'total_calls': len(metrics),
                    'success_count': success_count,
                    'error_count': error_count,
                    'success_rate': (success_count / len(metrics)) * 100 if metrics else 0,
                    'avg_execution_time': sum(execution_times) / len(execution_times) if execution_times else 0,
                    'min_execution_time': min(execution_times) if execution_times else 0,
                    'max_execution_time': max(execution_times) if execution_times else 0
                }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating performance report: {e}")
            return {'error': str(e)}
    
    async def auto_optimize(self) -> Dict[str, Any]:
        """Perform automatic optimizations based on metrics"""
        try:
            optimizations = []
            
            # Analyze cache performance
            cache_stats = self.cache_manager.get_stats()
            if cache_stats['hit_rate_percent'] < 50:
                # Low cache hit rate - consider increasing TTL
                optimizations.append({
                    'type': 'cache_optimization',
                    'action': 'increase_ttl',
                    'reason': f"Low cache hit rate: {cache_stats['hit_rate_percent']:.1f}%"
                })
            
            # Analyze slow operations
            for operation, metrics in self.performance_metrics.items():
                if not metrics:
                    continue
                    
                recent_metrics = metrics[-100:]  # Last 100 operations
                avg_time = sum(m['execution_time'] for m in recent_metrics) / len(recent_metrics)
                
                if avg_time > 5.0:  # Slower than 5 seconds
                    optimizations.append({
                        'type': 'performance_optimization',
                        'operation': operation,
                        'action': 'consider_caching_or_optimization',
                        'reason': f"Slow average execution time: {avg_time:.2f}s"
                    })
            
            # Store optimization history
            optimization_record = {
                'timestamp': time.time(),
                'optimizations': optimizations
            }
            self.optimization_history.append(optimization_record)
            
            # Keep only last 100 optimization records
            if len(self.optimization_history) > 100:
                self.optimization_history = self.optimization_history[-100:]
            
            return {
                'optimizations_found': len(optimizations),
                'optimizations': optimizations,
                'timestamp': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Auto-optimization error: {e}")
            return {'error': str(e)}
    
    def shutdown(self):
        """Shutdown performance optimizer"""
        try:
            self.task_pool.shutdown()
            self.logger.info("Performance optimizer shutdown completed")
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


# Global performance optimizer instance
performance_optimizer = None

def get_performance_optimizer() -> PerformanceOptimizer:
    """Get the global performance optimizer instance"""
    global performance_optimizer
    if performance_optimizer is None:
        performance_optimizer = PerformanceOptimizer()
        # Start background tasks
        performance_optimizer.start_background_tasks()
    return performance_optimizer


# Utility decorators for easy use
def cached(ttl: int = 300, key_prefix: str = ""):
    """Convenience decorator for caching"""
    optimizer = get_performance_optimizer()
    return optimizer.cached(ttl=ttl, key_prefix=key_prefix)


def timed(operation_name: Optional[str] = None):
    """Convenience decorator for timing"""
    optimizer = get_performance_optimizer()
    return optimizer.timed(operation_name=operation_name)