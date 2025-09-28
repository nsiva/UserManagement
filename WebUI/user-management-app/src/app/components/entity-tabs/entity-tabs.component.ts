import { Component, Input, Output, EventEmitter, OnInit, OnChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { FunctionalRolesManagerComponent, FunctionalRoleContext } from '../functional-roles-manager/functional-roles-manager';

export type EntityType = 'organization' | 'business_unit' | 'user';

export interface TabConfig {
  id: string;
  label: string;
  icon?: string;
  active: boolean;
}

@Component({
  selector: 'app-entity-tabs',
  standalone: true,
  imports: [CommonModule, FormsModule, FunctionalRolesManagerComponent],
  templateUrl: './entity-tabs.component.html',
  styleUrls: ['./entity-tabs.component.scss']
})
export class EntityTabsComponent implements OnInit, OnChanges {
  @Input() entityType: EntityType = 'organization';
  @Input() entityId: string | null = null;
  @Input() showFunctionalRoles: boolean = true;
  @Input() readonly: boolean = false;
  @Output() tabChanged = new EventEmitter<string>();
  @Output() functionalRolesChanged = new EventEmitter<any>();

  currentTab: string = 'basic';
  tabs: TabConfig[] = [];

  ngOnInit() {
    this.initializeTabs();
  }

  ngOnChanges() {
    this.initializeTabs();
  }

  private initializeTabs() {
    this.tabs = [
      { id: 'basic', label: 'Basic Information', active: true },
      { id: 'functional-roles', label: 'Functional Roles', active: false }
    ];

    // Set the first tab as active by default
    this.currentTab = 'basic';
    this.updateActiveTab();
  }

  selectTab(tabId: string) {
    this.currentTab = tabId;
    this.updateActiveTab();
    this.tabChanged.emit(tabId);
  }

  private updateActiveTab() {
    this.tabs.forEach(tab => {
      tab.active = tab.id === this.currentTab;
    });
  }

  onFunctionalRolesChanged(event: any) {
    this.functionalRolesChanged.emit(event);
  }

  get functionalRoleContext(): FunctionalRoleContext {
    switch (this.entityType) {
      case 'organization':
        return 'organization';
      case 'business_unit':
        return 'business_unit';
      case 'user':
        return 'user';
      default:
        return 'organization';
    }
  }

  get showBasicTab(): boolean {
    return this.currentTab === 'basic';
  }

  get showFunctionalRolesTab(): boolean {
    return this.currentTab === 'functional-roles' && this.showFunctionalRoles;
  }
}