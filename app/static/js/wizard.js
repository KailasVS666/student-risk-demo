/**
 * Form Wizard Module
 * Manages multi-step form navigation and state.
 */

import APP_CONFIG from './config.js';
import { validateStep, markFormDirty } from './form-utils.js';
import { safeGetElement } from './ui-utils.js';

/**
 * WizardManager Class
 * Encapsulates all wizard navigation logic.
 */
export class WizardManager {
  /**
   * @param {Object} options - Configuration options.
   * @param {number} [options.totalSteps=3] - Total number of form steps.
   */
  constructor(options = {}) {
    this.currentStep = 0;
    this.totalSteps = options.totalSteps || 3;
    this.formSteps = document.querySelectorAll('.form-step');
    this.progressSteps = document.querySelectorAll('.progress-step');
    this.progressBarContainer = document.querySelector('.progress-bar-container');
    // Multiple buttons share these ids across sticky bar + inline fallback, so bind to all
    this.nextButtons = document.querySelectorAll('#nextBtn');
    this.prevButtons = document.querySelectorAll('#prevBtn');
    this.generateAdviceButtons = document.querySelectorAll('#generateAdviceBtn');
    this.actionStepLabel = safeGetElement('actionStepLabel', false);
    this.actionStepTitle = safeGetElement('actionStepTitle', false);

    this.init();
  }

  /**
   * Initializes event listeners and renders initial state.
   * @private
   */
  init() {
    if (this.nextButtons?.length) {
      this.nextButtons.forEach(btn => btn.addEventListener('click', () => this.goToNextStep()));
    }

    if (this.prevButtons?.length) {
      this.prevButtons.forEach(btn => btn.addEventListener('click', () => this.goToPreviousStep()));
    }

    // Initialize range value displays
    this.setupRangeDisplays();

    // Render initial wizard state
    this.render();
  }

  /**
   * Sets up event listeners for range input displays.
   * @private
   */
  setupRangeDisplays() {
    document.querySelectorAll('input[type="range"]').forEach(input => {
      const valueSpan = document.getElementById(`${input.id}Value`);
      if (valueSpan) {
        input.addEventListener('input', () => {
          valueSpan.textContent = input.value;
          markFormDirty();
        });
      }
    });
  }

  /**
   * Moves to the next step if current step is valid.
   */
  goToNextStep() {
    if (!validateStep(this.currentStep)) {
      return;
    }

    if (this.currentStep < this.totalSteps - 1) {
      this.currentStep++;
      this.render();
    }
  }

  /**
   * Moves to the previous step.
   */
  goToPreviousStep() {
    if (this.currentStep > 0) {
      this.currentStep--;
      this.render();
    }
  }

  /**
   * Jumps to a specific step (for direct navigation).
   * @param {number} stepIndex - The step index to jump to.
   */
  goToStep(stepIndex) {
    if (stepIndex >= 0 && stepIndex < this.totalSteps) {
      this.currentStep = stepIndex;
      this.render();
    }
  }

  /**
   * Renders the current wizard state.
   * @private
   */
  render() {
    this.updateFormStepVisibility();
    this.updateProgressIndicators();
    this.updateProgressBar();
    this.updateNavigationButtons();
    this.updateActionBarText();
  }

  /**
   * Shows/hides form steps based on current step.
   * @private
   */
  updateFormStepVisibility() {
    this.formSteps.forEach((step, index) => {
      const isActive = index === this.currentStep;
      step.classList.toggle('active-step', isActive);
      if (isActive) {
        step.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  }

  /**
   * Updates progress step indicators.
   * @private
   */
  updateProgressIndicators() {
    this.progressSteps.forEach((step, index) => {
      const isActive = index === this.currentStep;
      const isCompleted = index < this.currentStep;

      step.classList.toggle('active', isActive);
      step.classList.toggle('completed', isCompleted);
    });
  }

  /**
   * Updates progress bar line animation.
   * @private
   */
  updateProgressBar() {
    if (!this.progressBarContainer) return;

    this.progressBarContainer.classList.remove('step-2', 'step-3');

    if (this.currentStep >= 1) {
      this.progressBarContainer.classList.add('step-2');
    }

    if (this.currentStep >= 2) {
      this.progressBarContainer.classList.add('step-3');
    }
  }

  /**
   * Updates navigation button visibility.
   * @private
   */
  updateNavigationButtons() {
    // Previous buttons
    if (this.prevButtons?.length) {
      this.prevButtons.forEach(btn => {
        btn.style.display = this.currentStep > 0 ? 'inline-flex' : 'none';
      });
    }

    // Next buttons and Generate Advice buttons
    const onLastStep = this.currentStep === this.totalSteps - 1;

    if (this.nextButtons?.length) {
      this.nextButtons.forEach(btn => {
        btn.style.display = onLastStep ? 'none' : 'inline-flex';
      });
    }

    if (this.generateAdviceButtons?.length) {
      this.generateAdviceButtons.forEach(btn => {
        btn.disabled = !onLastStep;
      });
    }

    this.updateActionBarText();
  }

  /**
   * Updates the sticky action bar step text.
   * @private
   */
  updateActionBarText() {
    if (!this.actionStepLabel || !this.actionStepTitle) return;

    this.actionStepLabel.textContent = `Step ${this.currentStep + 1} of ${this.totalSteps}`;
    const labels = [
      'Demographics',
      'Family & Education',
      'Academic & Social'
    ];
    this.actionStepTitle.textContent = labels[this.currentStep] || 'Step';
  }

  /**
   * Gets the current step index.
   * @returns {number} The current step index.
   */
  getCurrentStep() {
    return this.currentStep;
  }

  /**
   * Checks if the wizard is on the last step.
   * @returns {boolean} True if on last step.
   */
  isLastStep() {
    return this.currentStep === this.totalSteps - 1;
  }

  /**
   * Gets the total number of steps.
   * @returns {number} Total steps.
   */
  getTotalSteps() {
    return this.totalSteps;
  }

  /**
   * Resets wizard to first step.
   */
  reset() {
    this.currentStep = 0;
    this.render();
  }

  /**
   * Gets step name/label for display.
   * @param {number} [stepIndex] - Step index (defaults to current step).
   * @returns {string} Step label.
   */
  getStepLabel(stepIndex = this.currentStep) {
    const labels = [
      'Demographics',
      'Family & Education',
      'Academic & Social'
    ];
    return labels[stepIndex] || 'Unknown Step';
  }
}

/**
 * Factory function to create and initialize a wizard manager.
 * @param {Object} [options] - Configuration options.
 * @returns {WizardManager|null} The wizard manager instance or null if initialization fails.
 * @example
 * const wizard = initializeWizard({ totalSteps: 3 });
 */
export function initializeWizard(options = {}) {
  try {
    return new WizardManager(options);
  } catch (error) {
    console.error('Failed to initialize wizard:', error);
    return null;
  }
}

export default {
  WizardManager,
  initializeWizard
};
