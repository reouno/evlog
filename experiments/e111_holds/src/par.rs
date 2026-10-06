//! Work over the cells on several threads, with results that do not depend on how many.
//!
//! A range of items is cut into `CHUNKS` fixed pieces; threads take pieces in turn, and what each piece returns
//! comes back in the pieces' order, so sums are the same on 1 thread or 12. A piece writes only its own items,
//! through `Shared` (the caller guarantees that no two pieces touch one item).

pub const CHUNKS: usize = 64;

/// A slice that pieces on several threads write to, each at its own indices.
pub struct Shared<T>(*mut T, usize);

unsafe impl<T> Send for Shared<T> {}
unsafe impl<T> Sync for Shared<T> {}

impl<T> Shared<T> {
    pub fn new(v: &mut [T]) -> Self {
        Shared(v.as_mut_ptr(), v.len())
    }
    /// The item at `i`. Safe while no other piece reaches the same index.
    #[inline]
    #[allow(clippy::mut_from_ref)]
    pub fn at(&self, i: usize) -> &mut T {
        debug_assert!(i < self.1);
        unsafe { &mut *self.0.add(i) }
    }
}

/// Run `f(lo, hi)` over `CHUNKS` pieces of `0..n` on `threads` threads; the pieces' results in order.
pub fn pieces<R: Send>(threads: usize, n: usize, f: impl Fn(usize, usize) -> R + Sync) -> Vec<R> {
    let bounds: Vec<(usize, usize)> = (0..CHUNKS).map(|i| (n * i / CHUNKS, n * (i + 1) / CHUNKS)).collect();
    over(threads, &bounds, |&(lo, hi)| f(lo, hi))
}

/// Run `f` over each item of `items` on `threads` threads; the results in the items' order.
pub fn over<I: Sync, R: Send>(threads: usize, items: &[I], f: impl Fn(&I) -> R + Sync) -> Vec<R> {
    let threads = threads.clamp(1, items.len().max(1));
    if threads == 1 {
        return items.iter().map(&f).collect();
    }
    let f = &f;
    let mut out: Vec<(usize, R)> = std::thread::scope(|s| {
        let hs: Vec<_> = (0..threads)
            .map(|t| s.spawn(move || (t..items.len()).step_by(threads).map(|i| (i, f(&items[i]))).collect::<Vec<_>>()))
            .collect();
        hs.into_iter().flat_map(|h| h.join().unwrap()).collect()
    });
    out.sort_by_key(|(i, _)| *i);
    out.into_iter().map(|(_, r)| r).collect()
}
