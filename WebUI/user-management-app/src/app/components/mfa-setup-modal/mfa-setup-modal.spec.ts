import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MfaSetupModal } from './mfa-setup-modal';

describe('MfaSetupModal', () => {
  let component: MfaSetupModal;
  let fixture: ComponentFixture<MfaSetupModal>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [MfaSetupModal]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MfaSetupModal);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
