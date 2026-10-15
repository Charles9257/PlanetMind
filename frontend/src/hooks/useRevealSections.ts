import { useEffect } from "react";

export function useRevealSections() {
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      {
        threshold: 0.18,
        rootMargin: "0px 0px -6% 0px"
      }
    );

    // Tracked in a closure-local WeakSet rather than a DOM attribute: React StrictMode
    // double-invokes this effect in development (mount -> cleanup -> mount), and a DOM
    // attribute would survive that cleanup, causing the second (actually active) observer
    // to skip elements the first (already-disconnected) observer had marked -- orphaning
    // them at opacity:0 forever. A local WeakSet resets naturally on every invocation.
    const observed = new WeakSet<Element>();
    let index = 0;
    const observeNewSections = () => {
      document.querySelectorAll<HTMLElement>(".reveal-section").forEach((section) => {
        if (observed.has(section)) {
          return;
        }
        observed.add(section);
        section.style.transitionDelay = `${Math.min(index * 85, 520)}ms`;
        index += 1;
        observer.observe(section);
      });
    };

    // Content that appears later (a prediction result, an agent trace, a chart) is added
    // to the DOM after this effect's initial scan -- a MutationObserver catches it so it
    // doesn't stay stuck at the .reveal-section default of opacity:0 forever.
    observeNewSections();
    const mutationObserver = new MutationObserver(observeNewSections);
    mutationObserver.observe(document.body, { childList: true, subtree: true });

    return () => {
      observer.disconnect();
      mutationObserver.disconnect();
    };
  }, []);
}
