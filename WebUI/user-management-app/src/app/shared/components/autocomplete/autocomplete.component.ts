import { Component, Input, Output, EventEmitter, OnInit, OnDestroy, OnChanges, SimpleChanges, ElementRef, ViewChild, forwardRef } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

export interface AutocompleteOption {
  id: string;
  label: string;
  disabled?: boolean;
}

@Component({
  selector: 'app-autocomplete',
  standalone: true,
  imports: [CommonModule, FormsModule],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => AutocompleteComponent),
      multi: true
    }
  ],
  template: `
    <div class="relative w-full">
      <!-- Input Field -->
      <div class="relative">
        <input
          #inputElement
          type="text"
          [(ngModel)]="displayValue"
          (input)="onInput($event)"
          (focus)="onFocus()"
          (blur)="onBlur()"
          (keydown)="onKeyDown($event)"
          [placeholder]="placeholder"
          [disabled]="disabled"
          [class]="inputClass"
          [attr.aria-expanded]="isOpen"
          [attr.aria-haspopup]="true"
          [attr.aria-activedescendant]="highlightedIndex >= 0 ? 'option-' + highlightedIndex : null"
          autocomplete="off"
        />
        
        <!-- Dropdown Arrow -->
        <div 
          class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none"
          [class.hidden]="disabled"
        >
          <svg 
            class="h-4 w-4 text-theme-text-muted transition-transform duration-200"
            [class.rotate-180]="isOpen"
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
          </svg>
        </div>
        
        <!-- Clear Button -->
        <button
          *ngIf="displayValue && !disabled && showClearButton"
          type="button"
          class="absolute inset-y-0 right-8 flex items-center pr-1 text-theme-text-muted hover:text-theme-text"
          (click)="clearSelection()"
          (mousedown)="$event.preventDefault()"
        >
          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>

      <!-- Dropdown List -->
      <div 
        *ngIf="isOpen && !disabled"
        class="absolute z-50 w-full mt-1 bg-theme-surface border border-theme-border rounded-md shadow-lg max-h-60 overflow-auto"
        role="listbox"
      >
        <!-- Loading State -->
        <div *ngIf="loading" class="px-3 py-2 text-sm text-theme-text-muted">
          <div class="flex items-center">
            <svg class="animate-spin h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Loading...
          </div>
        </div>

        <!-- Options -->
        <div 
          *ngFor="let option of filteredOptions; let i = index"
          [id]="'option-' + i"
          role="option"
          [attr.aria-selected]="selectedValue === option.id"
          [class]="getOptionClass(i, option)"
          (click)="selectOption(option)"
          (mouseenter)="highlightedIndex = i"
        >
          {{ option.label }}
        </div>

        <!-- No Results -->
        <div 
          *ngIf="!loading && filteredOptions.length === 0 && displayValue.trim()"
          class="px-3 py-2 text-sm text-theme-text-muted"
        >
          No results found
        </div>

        <!-- Empty State -->
        <div 
          *ngIf="!loading && filteredOptions.length === 0 && !displayValue.trim() && emptyMessage"
          class="px-3 py-2 text-sm text-theme-text-muted"
        >
          {{ emptyMessage }}
        </div>
      </div>
    </div>
  `
})
export class AutocompleteComponent implements ControlValueAccessor, OnInit, OnDestroy, OnChanges {
  @Input() options: AutocompleteOption[] = [];
  @Input() placeholder: string = 'Search...';
  @Input() disabled: boolean = false;
  @Input() loading: boolean = false;
  @Input() showClearButton: boolean = true;
  @Input() emptyMessage: string = '';
  @Input() minSearchLength: number = 0;
  @Input() inputClass: string = 'mt-1 block w-full px-3 py-2 border border-theme-border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-theme-primary focus:border-theme-primary sm:text-sm bg-theme-background text-theme-text';
  @Input() value: string = '';

  @Output() optionSelected = new EventEmitter<AutocompleteOption>();
  @Output() searchChanged = new EventEmitter<string>();
  @Output() cleared = new EventEmitter<void>();

  @ViewChild('inputElement') inputElement!: ElementRef<HTMLInputElement>;

  displayValue: string = '';
  selectedValue: string = '';
  isOpen: boolean = false;
  filteredOptions: AutocompleteOption[] = [];
  highlightedIndex: number = -1;

  private onChange = (value: any) => {};
  private onTouched = () => {};

  ngOnInit() {
    this.updateFilteredOptions();
    // Set initial value if provided
    if (this.value) {
      this.selectedValue = this.value;
      this.updateDisplayValue();
    }
  }

  ngOnDestroy() {
    // Clean up any subscriptions if needed
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['value']) {
      const newValue = changes['value'].currentValue || '';
      console.log('AutocompleteComponent: ngOnChanges - value changed from', this.selectedValue, 'to', newValue);
      if (newValue !== this.selectedValue) {
        this.selectedValue = newValue;
        this.updateDisplayValue();
        console.log('AutocompleteComponent: Updated selectedValue and displayValue');
      }
    }
    if (changes['options']) {
      this.updateFilteredOptions();
      // If we have a selected value but no display value, try to update it
      if (this.selectedValue && !this.displayValue) {
        this.updateDisplayValue();
        console.log('AutocompleteComponent: Options changed, updated display value for existing selection');
      }
    }
  }

  // ControlValueAccessor implementation
  writeValue(value: any): void {
    console.log('AutocompleteComponent: writeValue called with:', value, 'current selectedValue:', this.selectedValue);
    if (value !== this.selectedValue) {
      this.selectedValue = value || '';
      this.updateDisplayValue();
    }
  }

  registerOnChange(fn: any): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: any): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }

  onInput(event: any): void {
    const value = event.target.value;
    this.displayValue = value;
    
    if (value.length >= this.minSearchLength) {
      this.updateFilteredOptions();
      this.isOpen = true;
      this.highlightedIndex = -1;
      this.searchChanged.emit(value);
    } else {
      this.isOpen = false;
      this.filteredOptions = [];
    }

    // Clear selection if input doesn't match any option
    const matchingOption = this.options.find(opt => opt.label.toLowerCase() === value.toLowerCase());
    if (!matchingOption && this.selectedValue) {
      this.selectedValue = '';
      this.onChange('');
    }
  }

  onFocus(): void {
    if (this.displayValue.length >= this.minSearchLength) {
      this.updateFilteredOptions();
      this.isOpen = true;
    }
  }

  onBlur(): void {
    // Delay closing to allow option selection
    setTimeout(() => {
      this.isOpen = false;
      this.highlightedIndex = -1;
      this.onTouched();
    }, 200);
  }

  onKeyDown(event: KeyboardEvent): void {
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        this.navigateDown();
        break;
      case 'ArrowUp':
        event.preventDefault();
        this.navigateUp();
        break;
      case 'Enter':
        event.preventDefault();
        if (this.highlightedIndex >= 0 && this.filteredOptions[this.highlightedIndex]) {
          this.selectOption(this.filteredOptions[this.highlightedIndex]);
        }
        break;
      case 'Escape':
        this.isOpen = false;
        this.highlightedIndex = -1;
        this.inputElement.nativeElement.blur();
        break;
      case 'Tab':
        this.isOpen = false;
        this.highlightedIndex = -1;
        break;
    }
  }

  selectOption(option: AutocompleteOption): void {
    if (option.disabled) return;
    
    this.selectedValue = option.id;
    this.displayValue = option.label;
    this.isOpen = false;
    this.highlightedIndex = -1;
    
    this.onChange(option.id);
    this.optionSelected.emit(option);
  }

  clearSelection(): void {
    this.selectedValue = '';
    this.displayValue = '';
    this.isOpen = false;
    this.highlightedIndex = -1;
    
    this.onChange('');
    this.cleared.emit();
    this.inputElement.nativeElement.focus();
  }

  private updateFilteredOptions(): void {
    if (!this.displayValue.trim()) {
      this.filteredOptions = [...this.options];
      return;
    }

    const searchTerm = this.displayValue.toLowerCase();
    this.filteredOptions = this.options.filter(option => 
      option.label.toLowerCase().includes(searchTerm) && !option.disabled
    );
  }

  private updateDisplayValue(): void {
    console.log('AutocompleteComponent: updateDisplayValue called with selectedValue:', this.selectedValue);
    console.log('AutocompleteComponent: Available options:', this.options.length, this.options.map(o => `${o.id}: ${o.label}`));
    
    if (this.selectedValue) {
      const selectedOption = this.options.find(opt => opt.id === this.selectedValue);
      this.displayValue = selectedOption ? selectedOption.label : '';
      console.log('AutocompleteComponent: Found option:', selectedOption, 'displayValue set to:', this.displayValue);
    } else {
      this.displayValue = '';
      console.log('AutocompleteComponent: No selectedValue, displayValue set to empty');
    }
  }

  private navigateDown(): void {
    if (this.filteredOptions.length === 0) return;
    
    this.highlightedIndex = this.highlightedIndex < this.filteredOptions.length - 1 
      ? this.highlightedIndex + 1 
      : 0;
  }

  private navigateUp(): void {
    if (this.filteredOptions.length === 0) return;
    
    this.highlightedIndex = this.highlightedIndex > 0 
      ? this.highlightedIndex - 1 
      : this.filteredOptions.length - 1;
  }

  getOptionClass(index: number, option: AutocompleteOption): string {
    const baseClasses = 'px-3 py-2 text-sm cursor-pointer transition-colors';
    const selectedClass = this.selectedValue === option.id ? 'bg-theme-primary text-theme-primary-text' : '';
    const highlightedClass = index === this.highlightedIndex ? 'bg-theme-surface-hover' : '';
    const disabledClass = option.disabled ? 'opacity-50 cursor-not-allowed' : 'hover:bg-theme-surface-hover';
    
    return `${baseClasses} ${selectedClass} ${highlightedClass} ${disabledClass}`.trim();
  }
}